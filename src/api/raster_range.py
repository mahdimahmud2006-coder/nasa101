"""Single HTTP byte ranges for local native-raster reads (including HEAD)."""
import re
from pathlib import Path
from urllib.parse import urlsplit

def byte_interval(value,size):
    match=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
    if not match or not any(match.groups()) or size<=0: raise ValueError('Invalid range')
    lo,hi=match.groups()
    if lo:
        start=int(lo);end=min(size-1,int(hi)) if hi else size-1
    else:
        start=max(0,size-int(hi));end=size-1
    if not 0<=start<=end<size: raise ValueError('Unsatisfiable range')
    return start,end

class RasterRangeMixin:
    def send_head(self):
        url=urlsplit(self.path).path
        if not (url.startswith('/cases/') and url.lower().endswith('.tif')):
            return super().send_head()
        path=Path(self.translate_path(self.path))
        if not path.is_file(): return super().send_head()
        stream=path.open('rb')
        try:
            size=path.stat().st_size
            interval=None
            # Ignore unsupported multi-range and conditional range requests,
            # serving the full representation rather than a stale partial one.
            value=self.headers.get('Range','')
            if value.startswith('bytes=') and ',' not in value and 'If-Range' not in self.headers:
                try: interval=byte_interval(value,size)
                except ValueError:
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{size}')
                    self.send_header('Content-Length','0');self.end_headers();stream.close();return None
            self.send_response(206 if interval else 200)
            self.send_header('Content-Type','image/tiff');self.send_header('Accept-Ranges','bytes')
            self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
            length=size
            if interval:
                a,b=interval;stream.seek(a);length=b-a+1
                self.send_header('Content-Range',f'bytes {a}-{b}/{size}')
                self._range_remaining=length
            self.send_header('Content-Length',str(length));self.end_headers()
            return stream
        except BaseException:
            stream.close();raise
    def copyfile(self,source,outputfile):
        remaining=getattr(self,'_range_remaining',None)
        if remaining is None:return super().copyfile(source,outputfile)
        while remaining:
            chunk=source.read(min(remaining,65536))
            if not chunk:break
            outputfile.write(chunk);remaining-=len(chunk)
    def handle_one_request(self):
        self._range_remaining=None
        return super().handle_one_request()
