import json
from pathlib import Path
from scripts.archive_vedastro_nuget_probe import build_archive

def test_archive_contains_all_identity_layers(tmp_path: Path) -> None:
    candidate=tmp_path/"candidate.json";runtime=tmp_path/"runtime.json"
    candidate.write_text(json.dumps({"status":"reproducible_library_executable_verified","package_sha256":"a","library_dll_sha256":"b"}))
    runtime.write_text(json.dumps({"version":"1.2.0.0","informational_version":"1.2.0","methods":["M"],"method_contracts":[{"name":"M"}]}))
    report=build_archive(candidate,runtime)
    assert report["assembly_version"]=="1.2.0.0"
    assert report["public_methods"]==["M"]
    assert report["runtime_image_id"].startswith("sha256:")
