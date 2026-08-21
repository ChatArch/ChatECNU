from pathlib import Path


def test_mkdocs_material_renderer_and_package_metadata_contract() -> None:
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "site_url: https://arch.gh.wzhecnu.cn/ChatECNU/" in mkdocs
    assert "name: material" in mkdocs
    assert "pymdownx.emoji" in mkdocs
    assert "material.extensions.emoji.twemoji" in mkdocs
    assert "material.extensions.emoji.to_svg" in mkdocs
    assert "mkdocs-material>=9.5,<10.0" in pyproject
    assert 'Homepage = "https://arch.gh.wzhecnu.cn/ChatECNU/"' in pyproject
    assert 'Documentation = "https://arch.gh.wzhecnu.cn/ChatECNU/"' in pyproject
    assert 'Repository = "https://github.com/ChatArch/ChatECNU"' in pyproject


def test_public_docs_keep_live_cli_tree_contract() -> None:
    required = [
        "ecnu",
        "├── --tree  # Print the registered CLI tree and exit.",
        "├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.",
        "├── home  # ECNU 门户。",
        "├── net  # 校园网联网。",
        "└── visitor  # 访客账号。",
    ]
    for rel in ("README.md", "README.en.md", "docs/cli-tree.md", "docs/cli-tree.en.md"):
        text = Path(rel).read_text(encoding="utf-8")
        assert "template `hello`" not in text, rel
        for line in required:
            assert line in text, f"{rel} missing {line!r}"
