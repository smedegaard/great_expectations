import pathlib

import pytest

from docs.prepare_prior_versions import (
    _update_tag_references_for_correct_version_substitution,
    _use_relative_path_for_imports_substitution,
    _use_relative_path_for_imports_substitution_path_starting_with_forwardslash,
)


@pytest.mark.unit
def test__update_tag_references_for_correct_version_substitution():
    contents = """import data from '../term_tags/terms.json'

<span class="tooltip">
    <a href={'/docs/' + data[props.tag].url}>{props.text}</a>
    <span class="tooltiptext">{data[props.tag].definition}</span>
</span>"""

    version = "0.15.50"
    updated_contents = _update_tag_references_for_correct_version_substitution(
        contents=contents, version=version
    )
    expected_contents = """import data from '../term_tags/terms.json'

<span class="tooltip">
    <a href={'/docs/0.15.50/' + data[props.tag].url}>{props.text}</a>
    <span class="tooltiptext">{data[props.tag].definition}</span>
</span>"""
    assert updated_contents == expected_contents


@pytest.mark.unit
def test__use_relative_path_for_imports_substitution():
    contents = """import TabItem from '@theme/TabItem';
import TechnicalTag from '@site/docs/term_tags/_tag.mdx';

This guide will help you connect to your data stored on GCS using Pandas.
"""

    path_to_versioned_docs = pathlib.Path(
        "docs/docusaurus/versioned_docs/version-0.14.13/"
    )
    file_path = pathlib.Path(
        "docs/docusaurus/versioned_docs/version-0.14.13/guides/connecting_to_your_data/cloud/gcs/pandas.md"
    )

    updated_contents = _use_relative_path_for_imports_substitution(
        contents, path_to_versioned_docs, file_path
    )

    expected_contents = """import TabItem from '@theme/TabItem';
import TechnicalTag from '../../../../term_tags/_tag.mdx';

This guide will help you connect to your data stored on GCS using Pandas.
"""

    assert updated_contents == expected_contents


@pytest.mark.unit
def test__use_relative_path_for_imports_substitution_path_starting_with_forwardslash():
    contents = """import UniversalMap from '/docs/images/universal_map/_universal_map.mdx';
import TechnicalTag from '/docs/term_tags/_tag.mdx';

<UniversalMap setup='inactive' connect='active' create='inactive' validate='inactive'/>
"""

    path_to_versioned_docs = pathlib.Path(
        "docs/docusaurus/versioned_docs/version-0.14.13/"
    )
    file_path = pathlib.Path(
        "docs/docusaurus/versioned_docs/version-0.14.13/tutorials/getting_started/tutorial_connect_to_data.md"
    )

    updated_contents = (
        _use_relative_path_for_imports_substitution_path_starting_with_forwardslash(
            contents, path_to_versioned_docs, file_path
        )
    )

    expected_contents = """import UniversalMap from '../../images/universal_map/_universal_map.mdx';
import TechnicalTag from '../../term_tags/_tag.mdx';

<UniversalMap setup='inactive' connect='active' create='inactive' validate='inactive'/>
"""

    assert updated_contents == expected_contents
