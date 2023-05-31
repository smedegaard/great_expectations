---
id: plugin
title: Plugin
---

import TechnicalTag from '../term_tags/_tag.mdx';

Plugins extend Great Expectations' components and/or functionality.

Python files that are placed in the `plugins` directory in your project (which is created automatically when you initialize your <TechnicalTag relative="../" tag="data_context" text="Data Context" />) can be used to extend Great Expectations.  Modules added there can be referenced in configuration files or imported directly in Python interpreters, scripts, or Jupyter Notebooks.  If you contribute a feature to Great Expectations, implementing it as a Plugin will allow you to start using that feature even before it has been merged into the open source Great Expectations code base and included in a new release.

### Relationships to other objects

Due to their nature as extensions of Great Expectations, it can be generally said that any given Plugin can interact with any other object in Great Expectations that it is written to interact with.  However, best practices are to not interact with any objects not needed to achieve the Plugin's purpose.

## Use cases

Plugins can be relevant to any point in the process of working with Great Expectations, depending on what any given Plugin is meant to do or extend.  Developing a Plugin is a process that exists outside the standard four-step workflow for using Great Expectations.  However, you can generally expect to actually *use* a Plugin in the same step as whatever object it is extending would be used, and to configure a Plugin in the same step as you would configure whatever object is extended by the Plugin.

## Customization

Plugins can be anything from entirely custom code to subclasses inheriting from existing Great Expectations classes.  This versatility allows you to extend and tailor Great Expectations to your specific needs.  The use of Plugins can also allow you to implement features that have been submitted to Great Expectations but not yet integrated into the code base.  For instance, if you contributed code for a new feature to Great Expectations, you could implement it in your production environment as a plugin even if it had not yet been merged into the official Great Expectations code base and released as a new version.

## Component specific functionality

Because Plugins often extend the functionality of existing Greate Expectations components, it is impossible to classify all of their potential features in a few generic statements.  In general, best practices are to include thorough documentation if you are developing or contributing code for use as a Plugin.  If you are using code that was created by someone else, you will have to reference their documentation (and possibly their code itself) in order to determine the features of that specific Plugin.

The API of any given Plugin is determined by the individual or team that created it.  That said, if the Plugin is extending an existing Great Expectations component, then best practices are for the Plugin's API to mirror that of the object it extends as closely as possible.

## Import Plugins

Any Plugin dropped into the `plugins` folder can be imported with a standard Python import statement.  In some cases, this will be all you need to do in order to make use of the Plugin's functionality.  For example, a <TechnicalTag relative="../" tag="custom_expectation" text="Custom Expectation" /> Plugin could be imported and used the same as any other Expectation in the [interactive process for creating Expectations](../guides/expectations/how_to_create_and_edit_expectations_with_instant_feedback_from_a_sample_batch_of_data.md).

