"""Prepare prior docs versions of GX for inclusion into the latest docs under the version dropdown.

There are changes to paths that need to be made to prior versions of docs.
"""
from __future__ import annotations

import glob
import pathlib
import re


def _docs_dir() -> pathlib.Path:
    """Base directory for docs (contains docusaurus folder)."""
    return pathlib.Path().absolute()


def change_paths_for_docs_file_references(verbose: bool = False) -> None:
    """Change file= style references to use versioned_docs paths.

    This is used in v0.14 docs like v0.14.13 since we moved to using named
    snippets only for v0.15.50 and later.
    """
    path = _docs_dir() / "docusaurus/versioned_docs/version-0.14.13/"
    files = glob.glob(f"{path}/**/*.md", recursive=True)
    pattern = re.compile(r"((.*)(file *= *)((../)*))(.*)")
    path_to_insert = "versioned_code/version-0.14.13/"

    print(f"Processing {len(files)} files in change_paths_for_docs_file_references...")
    for file_path in files:
        with open(file_path, "r+") as f:
            contents = f.read()
            contents = re.sub(pattern, rf"\1{path_to_insert}\6", contents)
            f.seek(0)
            f.truncate()
            f.write(contents)
        if verbose:
            print(f"processed {file_path}")
    print(f"Processed {len(files)} files in change_paths_for_docs_file_references")


def _paths_to_versioned_docs() -> list[pathlib.Path]:
    data_path = _docs_dir() / "docusaurus/versioned_docs"
    paths = [f for f in data_path.iterdir() if f.is_dir()]
    return paths


def _paths_to_versioned_docs_after_v0_14_13() -> list[pathlib.Path]:
    data_path = _docs_dir() / "docusaurus/versioned_docs"
    paths = [f for f in data_path.iterdir() if f.is_dir() and "0.14.13" not in str(f)]
    return paths


def _paths_to_versioned_code() -> list[pathlib.Path]:
    data_path = _docs_dir() / "docusaurus/versioned_code"
    paths = [f for f in data_path.iterdir() if f.is_dir()]
    return paths


def _paths_to_versioned_code_after_v0_14_13() -> list[pathlib.Path]:
    data_path = _docs_dir() / "docusaurus/versioned_code"
    paths = [f for f in data_path.iterdir() if f.is_dir() and "0.14.13" not in str(f)]
    return paths


def prepend_version_info_to_name_for_snippet_by_name_references(
    verbose: bool = False,
) -> None:
    """Prepend version info e.g. name="snippet_name" -> name="version-0.15.50 snippet_name" """

    pattern = re.compile(r"((.*)(name *= *\"))(.*)")
    paths = (
        _paths_to_versioned_docs_after_v0_14_13()
        + _paths_to_versioned_code_after_v0_14_13()
    )

    print(
        f"Processing {len(paths)} paths in prepend_version_info_to_name_for_snippet_by_name_references..."
    )
    for path in paths:
        version = path.name
        files = []
        for extension in (".md", ".mdx", ".py", ".yml", ".yaml"):
            files.extend(glob.glob(f"{path}/**/*{extension}", recursive=True))
        print(
            f"    Processing {len(files)} files for path {path} in prepend_version_info_to_name_for_snippet_by_name_references..."
        )
        for file_path in files:
            with open(file_path, "r+") as f:
                contents = f.read()
                contents = re.sub(pattern, rf"\1{version} \4", contents)
                f.seek(0)
                f.truncate()
                f.write(contents)
            if verbose:
                print(f"processed {file_path}")
        print(
            f"    Processed {len(files)} files for path {path} in prepend_version_info_to_name_for_snippet_by_name_references"
        )
    print(
        f"Processed {len(paths)} paths in prepend_version_info_to_name_for_snippet_by_name_references"
    )


def prepend_version_info_to_name_for_href_absolute_links(verbose: bool = False) -> None:
    """Prepend version info to absolute links: /docs/... becomes /docs/{version}/..."""

    href_pattern = re.compile(r"(?P<href>href=[\"\']/docs/)(?P<link>\S*[\"\'])")
    version_from_path_name_pattern = re.compile(
        r"(?P<version>\d{1,2}\.\d{1,2}\.\d{1,2})"
    )
    paths = _paths_to_versioned_docs() + _paths_to_versioned_code()

    print(
        f"Processing {len(paths)} paths in prepend_version_info_to_name_for_href_absolute_links..."
    )
    for path in paths:
        version = path.name
        version_only = version_from_path_name_pattern.search(version).group("version")
        if not version_only:
            raise ValueError("Path does not contain a version number")

        files = []
        for extension in (".md", ".mdx"):
            files.extend(glob.glob(f"{path}/**/*{extension}", recursive=True))
        print(
            f"    Processing {len(files)} files for path {path} in prepend_version_info_to_name_for_href_absolute_links..."
        )
        for file_path in files:
            with open(file_path, "r+") as f:
                contents = f.read()
                # href="/docs/link" -> href="/docs/0.14.13/link"
                contents = re.sub(
                    href_pattern, rf"\g<href>{version_only}/\g<link>", contents
                )
                f.seek(0)
                f.truncate()
                f.write(contents)
            if verbose:
                print(f"processed {file_path}")
        print(
            f"    Processed {len(files)} files for path {path} in prepend_version_info_to_name_for_href_absolute_links"
        )
    print(
        f"Processed {len(paths)} paths in prepend_version_info_to_name_for_href_absolute_links"
    )


def update_tag_references_for_correct_version(
    verbose: bool = False,
) -> None:
    """Change _tag.mdx to point to appropriate version."""

    version_from_path_name_pattern = re.compile(
        r"(?P<version>\d{1,2}\.\d{1,2}\.\d{1,2})"
    )
    paths = _paths_to_versioned_docs()

    method_name_for_logging = "update_tag_references_for_correct_version"
    print(f"Processing {len(paths)} paths in {method_name_for_logging}...")
    for path in paths:
        version = path.name
        version_only = version_from_path_name_pattern.search(version).group("version")
        if not version_only:
            raise ValueError("Path does not contain a version number")
        files = [path / "term_tags/_tag.mdx"]
        print(
            f"    Processing {len(files)} files for path {path} in {method_name_for_logging}..."
        )
        for file_path in files:
            with open(file_path, "r+") as f:
                contents = f.read()
                # <a href={'/docs/' + data[props.tag].url}>{props.text}</a>
                # to ->
                # <a href={'/docs/0.14.13/' + data[props.tag].url}>{props.text}</a>
                # where 0.14.13 is replaced with the corresponding doc version e.g. 0.14.13, 0.15.50, etc.
                contents = _update_tag_references_for_correct_version_substitution(
                    contents, version_only
                )
                f.seek(0)
                f.truncate()
                f.write(contents)
            if verbose:
                print(f"processed {file_path}")
        print(
            f"    Processed {len(files)} files for path {path} in {method_name_for_logging}"
        )
    print(f"Processed {len(paths)} paths in {method_name_for_logging}")


def _update_tag_references_for_correct_version_substitution(
    contents: str, version: str
) -> str:
    """Change _tag.mdx to point to appropriate version.

    Args:
        contents: String to perform substitution.
        version: String of version number e.g. "0.15.50"

    Returns:
        Updated contents
    """
    pattern = re.compile(r"(?P<href><a href=\{'/docs/)(?P<rest>')")
    contents = re.sub(pattern, rf"\g<href>{version}/\g<rest>", contents)
    return contents


def use_relative_path_for_imports(
    verbose: bool = False,
) -> None:
    """Use relative imports instead of @site

    e.g. `import TechnicalTag from '../term_tags/_tag.mdx';`
    instead of `import TechnicalTag from '@site/docs/term_tags/_tag.mdx';`
    """

    paths = _paths_to_versioned_docs()

    method_name_for_logging = "use_relative_imports_for_tag_references"
    print(f"Processing {len(paths)} paths in {method_name_for_logging}...")
    for path in paths:
        files = []
        for extension in (".md", ".mdx"):
            files.extend(path.glob(f"**/*{extension}"))
        print(
            f"    Processing {len(files)} files for path {path} in {method_name_for_logging}..."
        )
        for file_path in files:
            with open(file_path, "r+") as f:
                contents = f.read()
                contents = _use_relative_path_for_imports_substitution(
                    contents, path, file_path
                )
                contents = _use_relative_path_for_imports_substitution_path_starting_with_forwardslash(
                    contents, path, file_path
                )
                f.seek(0)
                f.truncate()
                f.write(contents)
            if verbose:
                print(f"processed {file_path}")
        print(
            f"    Processed {len(files)} files for path {path} in {method_name_for_logging}"
        )
    print(f"Processed {len(paths)} paths in {method_name_for_logging}")


def _use_relative_path_for_imports_substitution(
    contents: str, path_to_versioned_docs: pathlib.Path, path_to_document: pathlib.Path
) -> str:
    """Change import path to use relative instead of @site alias.

    e.g. `import TechnicalTag from '../term_tags/_tag.mdx';`
    instead of `import TechnicalTag from '@site/docs/term_tags/_tag.mdx';`

    Args:
        contents: String to perform substitution.
        path_to_versioned_docs: e.g. "docs/docusaurus/versioned_docs/version-0.14.13/"
        path_to_document: Path to the document containing the import to substitute.

    Returns:
        Updated contents
    """
    relative_path = path_to_document.relative_to(path_to_versioned_docs)
    dotted_relative_path = "/".join(".." for _ in range(len(relative_path.parts) - 1))
    pattern = re.compile(
        r"(?P<import>import .* from ')(?P<at_site>@site/docs/)(?P<rest>.*)"
    )
    contents = re.sub(pattern, rf"\g<import>{dotted_relative_path}/\g<rest>", contents)
    return contents


def _use_relative_path_for_imports_substitution_path_starting_with_forwardslash(
    contents: str, path_to_versioned_docs: pathlib.Path, path_to_document: pathlib.Path
) -> str:
    """Change import path to use relative instead of starting from /docs/.

    e.g. `import TechnicalTag from '../../term_tags/_tag.mdx';`
    instead of `import TechnicalTag from '/docs/term_tags/_tag.mdx';`

    Args:
        contents: String to perform substitution.
        path_to_versioned_docs: e.g. "docs/docusaurus/versioned_docs/version-0.14.13/"
        path_to_document: Path to the document containing the import to substitute.

    Returns:
        Updated contents
    """
    relative_path = path_to_document.relative_to(path_to_versioned_docs)
    dotted_relative_path = "/".join(".." for _ in range(len(relative_path.parts) - 1))
    pattern = re.compile(
        r"(?P<import>import .* from ')(?P<slash_docs>/docs/)(?P<rest>.*)"
    )
    contents = re.sub(pattern, rf"\g<import>{dotted_relative_path}/\g<rest>", contents)
    return contents

    pass


if __name__ == "__main__":
    change_paths_for_docs_file_references()
    prepend_version_info_to_name_for_snippet_by_name_references()
    prepend_version_info_to_name_for_href_absolute_links()
    update_tag_references_for_correct_version()
    use_relative_path_for_imports()
