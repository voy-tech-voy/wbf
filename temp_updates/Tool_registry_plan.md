This high-level improvement plan is designed for a coding agent to transform the current hardcoded tool architecture into a Registry-based Strategy Pattern.

Goal

Replace tool-specific files (e.g., ffmpeg_settings.py, ffmpeg_validation.py) with a single Generic Engine that handles any tool defined in a central Registry.

Phase 1: Data Modeling (The Registry)

Task: Define the "Source of Truth" for all external tools.

Create client/core/tool_descriptor.py:

Define a ToolDescriptor dataclass.

Attributes: id, display_name, env_var_name, default_binary_name, version_arg (e.g., -version), min_version_required.

Create client/core/tool_registry.py:

Initialize a central dictionary AVAILABLE_TOOLS.

Migrate FFmpeg and ImageMagick metadata into this registry as ToolDescriptor instances.

Phase 2: Logic Consolidation (Generic Managers)

Task: Eliminate boilerplate by creating generic classes that read from a ToolDescriptor.

Refactor Settings:

Create client/utils/base_tool_settings.py.

This class replaces ffmpeg_settings.py. It takes a ToolDescriptor in its __init__ and handles JSON saving/loading using descriptor.id as the filename.

Refactor Validation:

Create client/core/base_tool_validation.py.

Implement a generic validate_executable(path, descriptor) that uses the descriptor's version commands and regex.

Delete Legacy Files:

Prepare to remove ffmpeg_settings.py, imagemagick_settings.py, etc., once the generic versions are tested.

Phase 3: Dynamic UI Implementation

Task: Make the "Advanced Settings Window" self-assembling.

Create ToolConfigurationWidget:

A generic UI component (QGroupBox) that takes a ToolDescriptor.

It contains the RadioButtons (Bundled/System/Custom) and the Path selection logic.

Refactor advanced_settings_window.py:

Remove hardcoded UI groups.

In the __init__ method, loop through tool_registry.AVAILABLE_TOOLS.

Instantiate a ToolConfigurationWidget for each and add it to the layout dynamically.

Phase 4: Startup & Environment Orchestration

Task: Automate the initialization of all registered tools.

Update client/main.py (StartupWorker):

Instead of calling ffmpeg_settings.validate_on_startup(), create a loop:

code
Python
download
content_copy
expand_less
for tool in tool_registry.AVAILABLE_TOOLS:
    settings = BaseToolSettings(tool)
    settings.apply_to_environment()

Standardize Environment Variable Access:

Create a helper in tool_registry.py called get_tool_path(tool_id).

The ConversionEngine should now call get_tool_path('ffmpeg') instead of manually fetching os.environ.get('FFMPEG_BINARY').

Phase 5: Extensibility Interface (The Plugin Hook)

Task: Allow "Context Plugins" to decide which tool to use.

Implement a JobOrchestrator:

When a job starts, the orchestrator looks at the JobType (e.g., HEVC_CONVERSION).

It maps that type to a ToolID from the registry.

This allows you to add a "Handbrake" tool later and simply update the mapping without changing the conversion logic.

Success Criteria for the Coding Agent

Zero hardcoded tool names in advanced_settings_window.py.

Adding a new tool (e.g., ffprobe or ghostscript) should only require adding one entry to tool_registry.py.

The Environment Variables are set automatically based on the registry's env_var_name property.

No code duplication between different tool settings or validation logic.

File Cleanup Map

Create: client/core/tool_descriptor.py

Create: client/core/tool_registry.py

Create: client/utils/generic_tool_manager.py

Modify: client/gui/advanced_settings_window.py (Remove hardcoding)

Modify: client/main.py (Loop initialization)

Delete: client/utils/ffmpeg_settings.py (and similar)

Delete: client/core/conversion_engine_validation.py (replaced by generic)