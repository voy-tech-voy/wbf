"""
Unit Tests for Presets Plugin

Tests cover:
- Tier 1: Models, Manager (YAML loading, tool validation), Builder (Jinja2 rendering)
- Tier 2: UI components (PresetCard, PresetGallery), Orchestrator
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock


# ============================================================================
# TIER 1 TESTS: Logic Layer
# ============================================================================

class TestPresetModels:
    """Test data models"""
    
    def test_preset_status_enum(self):
        from client.plugins.presets.logic.models import PresetStatus
        assert PresetStatus.READY.value == "ready"
        assert PresetStatus.MISSING_TOOL.value == "missing"
        assert PresetStatus.INVALID.value == "invalid"
    
    def test_pipeline_step_creation(self):
        from client.plugins.presets.logic.models import PipelineStep
        step = PipelineStep(
            tool="ffmpeg",
            command_template="{{ tool_exe }} -i {{ input_path }} {{ output_path }}",
            description="Convert video"
        )
        assert step.tool == "ffmpeg"
        assert "tool_exe" in step.command_template
        assert step.description == "Convert video"
    
    def test_preset_definition_creation(self):
        from client.plugins.presets.logic.models import PresetDefinition, PipelineStep, PresetStatus
        
        step = PipelineStep(tool="ffmpeg", command_template="test")
        preset = PresetDefinition(
            id="test_preset",
            name="Test Preset",
            category="test",
            pipeline=[step]
        )
        
        assert preset.id == "test_preset"
        assert preset.name == "Test Preset"
        assert preset.status == PresetStatus.READY
        assert len(preset.pipeline) == 1
        assert preset.is_available is True
    
    def test_preset_definition_missing_tool(self):
        from client.plugins.presets.logic.models import PresetDefinition, PipelineStep, PresetStatus
        
        preset = PresetDefinition(
            id="missing",
            name="Missing Tool",
            category="test",
            pipeline=[],
            status=PresetStatus.MISSING_TOOL,
            missing_tools=["imagemagick"]
        )
        
        assert preset.is_available is False
        assert "imagemagick" in preset.missing_tools


class TestMockRegistry:
    """Mock ToolRegistryProtocol for testing"""
    
    @staticmethod
    def create_mock_registry(available_tools=None, tool_paths=None):
        """Create a mock registry for testing"""
        available_tools = available_tools or ["ffmpeg"]
        tool_paths = tool_paths or {"ffmpeg": "/usr/bin/ffmpeg"}
        
        mock = Mock()
        mock.is_tool_available = lambda tool_id: tool_id in available_tools
        mock.get_tool_path = lambda tool_id: tool_paths.get(tool_id)
        mock.get_tool_version = lambda tool_id: "1.0" if tool_id in available_tools else None
        mock.list_available_tools = lambda: available_tools
        mock.list_registered_tools = lambda: list(tool_paths.keys())
        
        return mock


class TestPresetManager:
    """Test PresetManager YAML loading and validation"""
    
    def test_manager_initialization(self):
        from client.plugins.presets.logic.manager import PresetManager
        
        mock_registry = TestMockRegistry.create_mock_registry()
        manager = PresetManager(mock_registry)
        
        assert manager._registry == mock_registry
    
    def test_load_valid_yaml(self):
        from client.plugins.presets.logic.manager import PresetManager
        from client.plugins.presets.logic.models import PresetStatus
        
        # Create temp YAML file
        yaml_content = """
meta:
  id: test_preset
  name: Test Preset
  category: test

pipeline:
  - tool: ffmpeg
    command_template: "{{ tool_exe }} -i {{ input_path }} {{ output_path }}"
    description: "Convert file"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            mock_registry = TestMockRegistry.create_mock_registry(["ffmpeg"])
            manager = PresetManager(mock_registry)
            
            preset = manager.load_preset(temp_path)
            
            assert preset.id == "test_preset"
            assert preset.name == "Test Preset"
            assert preset.status == PresetStatus.READY
            assert len(preset.pipeline) == 1
            assert preset.pipeline[0].tool == "ffmpeg"
        finally:
            os.unlink(temp_path)
    
    def test_load_yaml_missing_tool(self):
        from client.plugins.presets.logic.manager import PresetManager
        from client.plugins.presets.logic.models import PresetStatus
        
        yaml_content = """
meta:
  id: missing_tool_preset
  name: Missing Tool Preset
  category: test

pipeline:
  - tool: imagemagick
    command_template: "{{ tool_exe }} {{ input_path }} {{ output_path }}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            # Mock registry where imagemagick is NOT available
            mock_registry = TestMockRegistry.create_mock_registry(["ffmpeg"])  # Only ffmpeg
            manager = PresetManager(mock_registry)
            
            preset = manager.load_preset(temp_path)
            
            assert preset.status == PresetStatus.MISSING_TOOL
            assert "imagemagick" in preset.missing_tools
            assert preset.is_available is False
        finally:
            os.unlink(temp_path)
    
    def test_load_all_presets(self):
        from client.plugins.presets.logic.manager import PresetManager
        
        # Use the actual presets directory
        mock_registry = TestMockRegistry.create_mock_registry(["ffmpeg"])
        manager = PresetManager(mock_registry)
        
        presets = manager.load_all()
        
        # Should load at least the instagram_reel_pro.yaml
        assert len(presets) >= 1


class TestCommandBuilder:
    """Test CommandBuilder Jinja2 rendering"""
    
    def test_builder_initialization(self):
        from client.plugins.presets.logic.builder import CommandBuilder
        
        mock_registry = TestMockRegistry.create_mock_registry()
        builder = CommandBuilder(mock_registry)
        
        assert builder._registry == mock_registry
    
    def test_build_simple_command(self):
        from client.plugins.presets.logic.builder import CommandBuilder
        from client.plugins.presets.logic.models import PipelineStep
        
        mock_registry = TestMockRegistry.create_mock_registry(
            ["ffmpeg"], 
            {"ffmpeg": "/usr/bin/ffmpeg"}
        )
        builder = CommandBuilder(mock_registry)
        
        step = PipelineStep(
            tool="ffmpeg",
            command_template='{{ tool_exe }} -i "{{ input_path }}" "{{ output_path }}"'
        )
        
        context = {
            "input_path": "/path/to/input.mp4",
            "output_path": "/path/to/output.mp4"
        }
        
        cmd = builder.build_command(step, context)
        
        assert "/usr/bin/ffmpeg" in cmd
        assert "/path/to/input.mp4" in cmd
        assert "/path/to/output.mp4" in cmd
    
    def test_build_command_with_defaults(self):
        from client.plugins.presets.logic.builder import CommandBuilder
        from client.plugins.presets.logic.models import PipelineStep
        
        mock_registry = TestMockRegistry.create_mock_registry(
            ["ffmpeg"], 
            {"ffmpeg": "ffmpeg.exe"}
        )
        builder = CommandBuilder(mock_registry)
        
        step = PipelineStep(
            tool="ffmpeg",
            command_template='{{ tool_exe }} -crf {{ quality | default(23) }} "{{ input_path }}"'
        )
        
        # Don't provide quality - should use default
        context = {"input_path": "test.mp4"}
        
        cmd = builder.build_command(step, context)
        
        assert "-crf 23" in cmd
    
    def test_build_command_tool_not_available(self):
        from client.plugins.presets.logic.builder import CommandBuilder
        from client.plugins.presets.logic.models import PipelineStep
        from client.plugins.presets.logic.exceptions import ToolNotAvailableError
        
        # Registry with no tools available
        mock_registry = TestMockRegistry.create_mock_registry([], {})
        builder = CommandBuilder(mock_registry)
        
        step = PipelineStep(tool="missing_tool", command_template="test")
        
        with pytest.raises(ToolNotAvailableError):
            builder.build_command(step, {})
    
    def test_build_pipeline_multiple_steps(self):
        from client.plugins.presets.logic.builder import CommandBuilder
        from client.plugins.presets.logic.models import PresetDefinition, PipelineStep
        
        mock_registry = TestMockRegistry.create_mock_registry(
            ["ffmpeg"], 
            {"ffmpeg": "ffmpeg"}
        )
        builder = CommandBuilder(mock_registry)
        
        preset = PresetDefinition(
            id="multi",
            name="Multi Step",
            category="test",
            pipeline=[
                PipelineStep(tool="ffmpeg", command_template="step1 {{ input_path }}"),
                PipelineStep(tool="ffmpeg", command_template="step2 {{ output_path }}")
            ]
        )
        
        context = {"input_path": "in.mp4", "output_path": "out.mp4"}
        
        commands = builder.build_pipeline(preset, context)
        
        assert len(commands) == 2
        assert "step1" in commands[0]
        assert "step2" in commands[1]


class TestExceptions:
    """Test custom exceptions"""
    
    def test_preset_load_error(self):
        from client.plugins.presets.logic.exceptions import PresetLoadError
        
        error = PresetLoadError("/path/to/preset.yaml", "File not found")
        assert "preset.yaml" in str(error)
        assert "File not found" in str(error)
    
    def test_tool_not_available_error(self):
        from client.plugins.presets.logic.exceptions import ToolNotAvailableError
        
        error = ToolNotAvailableError("imagemagick")
        assert "imagemagick" in str(error)
        assert error.tool_id == "imagemagick"
    
    def test_command_build_error(self):
        from client.plugins.presets.logic.exceptions import CommandBuildError
        
        error = CommandBuildError("Convert video", "Missing variable")
        assert "Convert video" in str(error)
        assert "Missing variable" in str(error)


# ============================================================================
# TIER 2 TESTS: UI Layer (Basic - No Qt Widget Testing)
# ============================================================================

class TestOrchestratorIntegration:
    """Test PresetOrchestrator without Qt (import test only)"""
    
    def test_orchestrator_imports(self):
        """Verify orchestrator can be imported"""
        from client.plugins.presets.orchestrator import PresetOrchestrator
        assert PresetOrchestrator is not None
    
    def test_logic_exports(self):
        """Verify logic module exports"""
        from client.plugins.presets.logic import (
            PresetManager,
            CommandBuilder,
            PresetDefinition,
            PresetStatus,
            PipelineStep
        )
        assert all([PresetManager, CommandBuilder, PresetDefinition, PresetStatus, PipelineStep])


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
