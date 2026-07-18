from scripts.vedastro_identity_archive import build_archive


def test_vedastro_identity_archive_records_self_host_identity(monkeypatch) -> None:
    fixtures = {
        "https://api.nuget.org/v3/registration5-semver1/vedastro.library/1.2.0.json": {
            "catalogEntry": "https://example.invalid/catalog.json",
            "packageContent": "https://example.invalid/pkg.nupkg",
            "published": "2023-03-22T22:22:01.81+00:00",
        },
        "https://example.invalid/catalog.json": {
            "packageHashAlgorithm": "SHA512",
            "packageHash": "hash",
            "packageSize": 230836,
            "published": "2023-03-22T22:22:01.81Z",
            "catalog:commitId": "commit",
            "catalog:commitTimeStamp": "2023-03-22T22:24:11.811524Z",
            "licenseExpression": "MIT",
            "projectUrl": "https://vedastro.org/",
            "dependencyGroups": [
                {
                    "targetFramework": "net7.0",
                    "dependencies": [{"id": "SwissEphNet", "range": "[2.8.0.2, )"}],
                }
            ],
        },
    }

    monkeypatch.setattr("scripts.vedastro_identity_archive._json_url", lambda url, timeout: fixtures[url])
    report = build_archive("1.2.0")

    assert report["package_hash_algorithm"] == "SHA512"
    assert report["license"] == "MIT"
    assert report["self_host_candidate_status"] == "reproducible_package_identity_archived"
    assert report["hosted_api_status"] == "blocked"
    assert report["dependencies"] == [
        {"target_framework": "net7.0", "id": "SwissEphNet", "range": "[2.8.0.2, )"}
    ]
