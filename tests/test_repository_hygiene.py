import io,json,subprocess,zipfile,hashlib
from pathlib import Path
import pytest
from scripts.fetch_runtime import destination,install_archive
ROOT=Path(__file__).resolve().parents[1]

def ignored(path):return subprocess.run(['git','check-ignore','--no-index','-q',path],cwd=ROOT).returncode==0

@pytest.mark.parametrize('name',['database/new/catalog.json','anything.HDF5','.venv-search/bin/python','web/public/cases/sample/map.tif','web/public/cases/sample/view.png','data/derived/cube.npz','dist/release.zip','output/report.pdf','runtime-downloads/part.zip','web/public/cases/sample/credentials.json','data/palettes/v1/.env','nested/.aws/credentials','.netrc'])
def test_local_large_and_secret_files_are_ignored(name):assert ignored(name)

@pytest.mark.parametrize('name',['README.md','.env.example','config.records.json','docs/assets/terrapulse-banner.svg','docs/assets/jamuna-radar-composite.png','web/public/cases/sample/manifest.json','data/context/source.json','data/palettes/v1/matplotlib_source'])
def test_source_provenance_and_curated_docs_remain_publishable(name):assert not ignored(name)

@pytest.mark.parametrize('name',['../escape','/tmp/escape','.git/config','web/public/cases/../../../../escape','web/public/cases/file.py'])
def test_runtime_paths_cannot_escape_or_replace_code(tmp_path,name):
    with pytest.raises(ValueError):destination(tmp_path,name)

def test_runtime_restoration_checks_bytes_and_refuses_conflicting_file(tmp_path):
    content=b'processed-test-object';sha=hashlib.sha256(content).hexdigest();archive=tmp_path/'part.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('objects/'+sha,content)
    name='web/public/cases/sample/hh.tif';files={name:{'sha256':sha,'bytes':len(content)}}
    assert install_archive(archive,files,tmp_path)==1;assert (tmp_path/name).read_bytes()==content
    assert install_archive(archive,files,tmp_path)==0
    (tmp_path/name).write_bytes(b'local modification')
    with pytest.raises(ValueError,match='refusing to overwrite'):install_archive(archive,files,tmp_path)
    assert (tmp_path/name).read_bytes()==b'local modification'

def test_runtime_checksum_failure_does_not_publish_data(tmp_path):
    sha='a'*64;archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('objects/'+sha,b'bad')
    name='web/public/cases/sample/hh.tif'
    with pytest.raises(ValueError,match='checksum'):install_archive(archive,{name:{'sha256':sha,'bytes':3}},tmp_path)
    assert not (tmp_path/name).exists()
