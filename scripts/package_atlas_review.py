"""Bundle the verified static Atlas, its offline edition, and a saved judge example."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

from package_atlas_static import ROOT, assert_public_text, verify_folder


def review_archive(example, root=ROOT):
    out = root / 'output/atlas'
    pointer = json.loads((out / 'release.json').read_text())
    manifest_path = out / pointer['manifest']
    manifest = json.loads(manifest_path.read_text())
    release_id = manifest['releaseId']
    if release_id != pointer['releaseId']:
        raise ValueError('The release pointer and manifest differ.')

    static = manifest_path.parent / manifest['static']['folder']
    inventory = manifest['static']['assets']
    verify_folder(static, inventory)
    portable = manifest_path.parent / manifest['portable']['path']
    portable_bytes = portable.read_bytes()
    if sha256(portable_bytes).hexdigest() != manifest['portable']['sha256']:
        raise ValueError('The offline edition does not match this release.')

    sample = example.read_bytes()
    assert_public_text(sample, 'Kathmandu-dossier.json')
    record = json.loads(sample)
    contract = record.get('contract', {})
    footprint = contract.get('footprint', {})
    case = manifest['records']['nepal_surface']
    if (record.get('schema') != 'terrapulse.atlas-investigation.v2' or
            contract.get('caseId') != 'nepal_surface' or
            contract.get('manifestSha256') != case['manifestSha256'] or
            contract.get('evidenceVersion') != case['evidenceVersion'] or
            footprint.get('kind') != 'saved' or
            contract.get('layerId') != 'hh' or
            record.get('selected_utc') != '2026-09-12T23:39:18Z' or
            record.get('common_valid_pixels') != 199):
        raise ValueError('The example must be the verified saved Kathmandu chapter.')

    files = {
        'START_HERE.md': (root / 'docs/ATLAS_JUDGING_QUICKSTART.md').read_bytes(),
        'TerraPulse.html': portable_bytes,
        'release-manifest.json': manifest_path.read_bytes(),
        'examples/Kathmandu-dossier.json': sample,
    }
    files.update({'static/' + name: (static / name).read_bytes() for name in inventory})
    target = manifest_path.parent / f'TerraPulse-judging-{release_id}.zip'
    with TemporaryDirectory(prefix='.judge-', dir=target.parent) as staging:
        temp = Path(staging) / target.name
        with ZipFile(temp, 'w') as archive:
            for name, data in sorted(files.items()):
                entry = ZipInfo(name)
                entry.compress_type = ZIP_STORED if name.endswith(('.webp', '.woff2')) else ZIP_DEFLATED
                archive.writestr(entry, data)
        with ZipFile(temp) as archive:
            if archive.testzip() or set(archive.namelist()) != set(files):
                raise ValueError('The judging archive failed its integrity check.')
            for name, data in files.items():
                if sha256(archive.read(name)).digest() != sha256(data).digest():
                    raise ValueError(f'Archive member mismatch: {name}')
        temp.replace(target)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('example', type=Path, help='Browser-verified Kathmandu dossier')
    args = parser.parse_args()
    print(review_archive(args.example))
