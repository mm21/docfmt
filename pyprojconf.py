from pyprojkit import (
    ProjectConfig,
    PythonVersions,
    RequiresPython,
    create_kitchen_sink_tools,
)

config = ProjectConfig(
    package="docfmt",
    requires_python=RequiresPython((3, 12)),
    pinned_python=PythonVersions(3, (12, 14)),
    tools=create_kitchen_sink_tools(),
)
