"""
AI Providers Package

Provides AI provider implementations with lazy loading and dependency management.
Includes automatic dependency installation and enhanced error handling.
"""

import subprocess
import traceback
from typing import Any, Dict

import FreeCAD

# Import base classes first
from ai.providers.base_provider import (
    AIMessage,
    AIResponse,
    BaseAIProvider,
    MessageRole,
)

# Lazy loading for providers to handle missing dependencies gracefully
_providers = {}
_provider_errors = {}
_dependency_install_attempted = False


def _attempt_dependency_installation():
    """Attempt to install missing dependencies automatically."""
    global _dependency_install_attempted

    if _dependency_install_attempted:
        return False  # Don't try multiple times

    _dependency_install_attempted = True

    try:
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Attempting automatic dependency installation...\n"
        )

        # Try to import and use the dependency manager
        try:
            from utils.dependency_manager import DependencyManager

            def progress_callback(message):
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: {message}\n")

            manager = DependencyManager(progress_callback)

            # Check for missing critical dependencies and sub-dependencies
            critical_missing = manager.get_critical_missing_dependencies()

            if critical_missing:
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Installing critical dependencies: {', '.join(critical_missing)}\n"
                )

                # Special handling for aiohttp and its sub-dependencies
                if "aiohttp" in critical_missing:
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Checking aiohttp sub-dependencies...\n"
                    )

                    # Check sub-dependencies
                    sub_deps = manager.check_sub_dependencies("aiohttp")
                    missing_sub_deps = [
                        dep for dep, available in sub_deps.items() if not available
                    ]

                    if missing_sub_deps:
                        FreeCAD.Console.PrintMessage(
                            f"FreeCAD AI: Missing sub-dependencies: {', '.join(missing_sub_deps)}\n"
                        )

                # Try to install critical dependencies with sub-dependency support
                success = manager.install_missing_dependencies(critical_only=True)

                if success:
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: ✅ Critical dependencies installed successfully\n"
                    )

                    # Verify sub-dependencies were installed correctly
                    if "aiohttp" in critical_missing and manager.check_dependency(
                        "aiohttp"
                    ):
                        sub_deps_after = manager.check_sub_dependencies("aiohttp")
                        still_missing = [
                            dep
                            for dep, available in sub_deps_after.items()
                            if not available
                        ]

                        if still_missing:
                            FreeCAD.Console.PrintWarning(
                                f"FreeCAD AI: ⚠️ Some sub-dependencies still missing: {', '.join(still_missing)}\n"
                            )
                            FreeCAD.Console.PrintMessage(
                                "FreeCAD AI: Attempting to install missing sub-dependencies individually...\n"
                            )

                            # Try to install missing sub-dependencies individually
                            for sub_dep in still_missing:
                                if manager.install_dependency(sub_dep):
                                    FreeCAD.Console.PrintMessage(
                                        f"FreeCAD AI: ✅ Sub-dependency {sub_dep} installed\n"
                                    )
                                else:
                                    FreeCAD.Console.PrintWarning(
                                        f"FreeCAD AI: ❌ Failed to install sub-dependency {sub_dep}\n"
                                    )
                        else:
                            FreeCAD.Console.PrintMessage(
                                "FreeCAD AI: ✅ All aiohttp sub-dependencies verified\n"
                            )

                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Please restart FreeCAD to use the new dependencies\n"
                    )
                    return True
                else:
                    FreeCAD.Console.PrintWarning(
                        "FreeCAD AI: ❌ Failed to install some critical dependencies\n"
                    )
                    return False
            else:
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: All critical dependencies are already available\n"
                )

                # Even if main dependencies are available, check sub-dependencies
                if manager.check_dependency("aiohttp"):
                    sub_deps = manager.check_sub_dependencies("aiohttp")
                    missing_sub_deps = [
                        dep for dep, available in sub_deps.items() if not available
                    ]

                    if missing_sub_deps:
                        FreeCAD.Console.PrintMessage(
                            f"FreeCAD AI: Installing missing aiohttp sub-dependencies: {', '.join(missing_sub_deps)}\n"
                        )

                        for sub_dep in missing_sub_deps:
                            if manager.install_dependency(sub_dep):
                                FreeCAD.Console.PrintMessage(
                                    f"FreeCAD AI: ✅ Sub-dependency {sub_dep} installed\n"
                                )
                            else:
                                FreeCAD.Console.PrintWarning(
                                    f"FreeCAD AI: ❌ Failed to install sub-dependency {sub_dep}\n"
                                )

                return True

        except ImportError as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Could not import dependency manager: {e}\n"
            )
            return False
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Dependency installation failed: {e}\n"
            )
            return False

    except Exception as e:
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: Automatic dependency installation error: {e}\n"
        )
        return False


def _show_dependency_guidance(missing_dependency, provider_name):
    """Show user-friendly guidance for installing missing dependencies."""
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")
    FreeCAD.Console.PrintMessage("FreeCAD AI: DEPENDENCY INSTALLATION GUIDE\n")
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")

    if missing_dependency == "aiohttp":
        FreeCAD.Console.PrintMessage(
            f"The {provider_name} provider requires the 'aiohttp' library.\n"
        )
        FreeCAD.Console.PrintMessage("\n📋 INSTALLATION OPTIONS:\n")
        FreeCAD.Console.PrintMessage("\n1. 🔧 Use the FreeCAD AI Dependencies Tab:\n")
        FreeCAD.Console.PrintMessage("   - Open the FreeCAD AI interface\n")
        FreeCAD.Console.PrintMessage(
            "   - Go to the 'Dependencies' or 'Settings' tab\n"
        )
        FreeCAD.Console.PrintMessage("   - Click 'Install Missing Dependencies'\n")

        FreeCAD.Console.PrintMessage(
            "\n2. 🐍 Manual Installation via FreeCAD Python Console:\n"
        )
        FreeCAD.Console.PrintMessage(
            "   Copy and paste this into the FreeCAD Python console:\n"
        )
        FreeCAD.Console.PrintMessage("   " + "-" * 50 + "\n")

        # Generate installation script
        try:
            from utils.dependency_manager import DependencyManager

            manager = DependencyManager()
            script = manager.create_install_script("aiohttp")
            # Show just the key parts
            FreeCAD.Console.PrintMessage("   exec('''")
            for line in script.split("\n")[10:25]:  # Show relevant parts
                if line.strip() and not line.startswith("#"):
                    FreeCAD.Console.PrintMessage(f"   {line}\n")
            FreeCAD.Console.PrintMessage("   ''')\n")
        except (AttributeError, IndexError, TypeError):
            # AttributeError: Script access issues
            # IndexError: Script parsing issues
            # TypeError: Script format issues  
            # Fallback simple script
            FreeCAD.Console.PrintMessage("   import subprocess, sys, os\n")
            FreeCAD.Console.PrintMessage(
                "   subprocess.run([sys.executable, '-m', 'pip', 'install', 'aiohttp>=3.8.0'])\n"
            )

        FreeCAD.Console.PrintMessage("   " + "-" * 50 + "\n")

        FreeCAD.Console.PrintMessage("\n3. 💻 System Package Manager:\n")
        FreeCAD.Console.PrintMessage(
            "   Ubuntu/Debian: sudo apt install python3-aiohttp\n"
        )
        FreeCAD.Console.PrintMessage("   Fedora: sudo dnf install python3-aiohttp\n")
        FreeCAD.Console.PrintMessage("   macOS: pip3 install aiohttp\n")

        FreeCAD.Console.PrintMessage("\n4. 🔄 Restart FreeCAD:\n")
        FreeCAD.Console.PrintMessage(
            "   After installation, restart FreeCAD to use the new dependency\n"
        )

    else:
        FreeCAD.Console.PrintMessage(
            f"The {provider_name} provider requires the '{missing_dependency}' library.\n"
        )
        FreeCAD.Console.PrintMessage(
            f"Please install it using: pip install {missing_dependency}\n"
        )
        FreeCAD.Console.PrintMessage(
            "Then restart FreeCAD to use the new dependency.\n"
        )

    FreeCAD.Console.PrintMessage("=" * 60 + "\n")


def _show_sub_dependency_guidance(
    main_dependency, missing_sub_dependency, provider_name
):
    """Show user-friendly guidance for installing missing sub-dependencies."""
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")
    FreeCAD.Console.PrintMessage("FreeCAD AI: SUB-DEPENDENCY INSTALLATION GUIDE\n")
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")

    FreeCAD.Console.PrintMessage(
        f"The {provider_name} provider requires '{missing_sub_dependency}', which is a sub-dependency of '{main_dependency}'.\n"
    )
    FreeCAD.Console.PrintMessage(
        f"This usually means {main_dependency} was installed without its required sub-dependencies.\n"
    )

    FreeCAD.Console.PrintMessage("\n📋 INSTALLATION OPTIONS:\n")
    FreeCAD.Console.PrintMessage("\n1. 🔧 Use the FreeCAD AI Dependencies Tab:\n")
    FreeCAD.Console.PrintMessage("   - Open the FreeCAD AI interface\n")
    FreeCAD.Console.PrintMessage("   - Go to the 'Dependencies' or 'Settings' tab\n")
    FreeCAD.Console.PrintMessage("   - Click 'Install Missing Dependencies'\n")

    FreeCAD.Console.PrintMessage(
        "\n2. 🐍 Manual Installation via FreeCAD Python Console:\n"
    )
    FreeCAD.Console.PrintMessage(
        "   Copy and paste this into the FreeCAD Python console:\n"
    )
    FreeCAD.Console.PrintMessage("   " + "-" * 50 + "\n")

    # Generate installation script for sub-dependency
    try:
        from utils.dependency_manager import DependencyManager

        manager = DependencyManager()

        # Create script for both main dependency and sub-dependency
        FreeCAD.Console.PrintMessage("   exec('''\n")
        FreeCAD.Console.PrintMessage("   import subprocess, sys, os\n")
        FreeCAD.Console.PrintMessage("   \n")
        FreeCAD.Console.PrintMessage("   # Install sub-dependency first\n")
        FreeCAD.Console.PrintMessage(
            f"   subprocess.run([sys.executable, '-m', 'pip', 'install', '{missing_sub_dependency}'])\n"
        )
        FreeCAD.Console.PrintMessage("   \n")
        FreeCAD.Console.PrintMessage(
            "   # Reinstall main dependency to ensure compatibility\n"
        )
        FreeCAD.Console.PrintMessage(
            f"   subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '{main_dependency}'])\n"
        )
        FreeCAD.Console.PrintMessage("   ''')\n")
    except (AttributeError, KeyError, TypeError):
        # AttributeError: Missing dependency manager attributes
        # KeyError: Missing dependency information
        # TypeError: Invalid dependency data format
        # Fallback simple script
        FreeCAD.Console.PrintMessage("   import subprocess, sys\n")
        FreeCAD.Console.PrintMessage(
            f"   subprocess.run([sys.executable, '-m', 'pip', 'install', '{missing_sub_dependency}'])\n"
        )
        FreeCAD.Console.PrintMessage(
            f"   subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '{main_dependency}'])\n"
        )

    FreeCAD.Console.PrintMessage("   " + "-" * 50 + "\n")

    FreeCAD.Console.PrintMessage("\n3. 💻 System Package Manager:\n")
    if main_dependency == "aiohttp":
        FreeCAD.Console.PrintMessage(
            "   Ubuntu/Debian: sudo apt install python3-aiohttp python3-multidict python3-yarl\n"
        )
        FreeCAD.Console.PrintMessage(
            "   Fedora: sudo dnf install python3-aiohttp python3-multidict python3-yarl\n"
        )
        FreeCAD.Console.PrintMessage("   macOS: pip3 install aiohttp[speedups]\n")
    else:
        FreeCAD.Console.PrintMessage(
            f"   Install both: pip3 install {missing_sub_dependency} {main_dependency}\n"
        )

    FreeCAD.Console.PrintMessage("\n4. 🔄 Restart FreeCAD:\n")
    FreeCAD.Console.PrintMessage(
        "   After installation, restart FreeCAD to use the new dependencies\n"
    )

    FreeCAD.Console.PrintMessage("\n💡 TROUBLESHOOTING:\n")
    FreeCAD.Console.PrintMessage(
        "   - Sub-dependencies are often missed when using --no-deps flag\n"
    )
    FreeCAD.Console.PrintMessage(
        "   - Try reinstalling the main dependency without --no-deps\n"
    )
    FreeCAD.Console.PrintMessage("   - Check that your pip version is up to date\n")

    FreeCAD.Console.PrintMessage("=" * 60 + "\n")


def _lazy_import_provider(provider_name: str, module_name: str, class_name: str):
    """Lazy import a provider with enhanced dependency management and error handling."""
    if provider_name in _providers:
        return _providers[provider_name]

    if provider_name in _provider_errors:
        # Don't retry if we already failed, unless dependencies were installed
        return None

    try:
        module = __import__(f"ai.providers.{module_name}", fromlist=[class_name])
        provider_class = getattr(module, class_name)
        _providers[provider_name] = provider_class
        FreeCAD.Console.PrintMessage(
            f"FreeCAD AI: ✅ {provider_name} provider loaded successfully\n"
        )
        return provider_class

    except ImportError as e:
        error_msg = f"Failed to import {provider_name}: {str(e)}"
        _provider_errors[provider_name] = error_msg

        # Enhanced sub-dependency detection
        missing_dependency = None
        missing_sub_dependency = None

        if "aiohttp" in str(e):
            missing_dependency = "aiohttp"
        elif "multidict" in str(e):
            missing_dependency = "aiohttp"
            missing_sub_dependency = "multidict"
        elif "yarl" in str(e):
            missing_dependency = "aiohttp"
            missing_sub_dependency = "yarl"
        elif "aiosignal" in str(e):
            missing_dependency = "aiohttp"
            missing_sub_dependency = "aiosignal"
        elif "requests" in str(e):
            missing_dependency = "requests"
        elif "mcp" in str(e):
            missing_dependency = "mcp"

        if missing_dependency:
            if missing_sub_dependency:
                FreeCAD.Console.PrintWarning(
                    f"FreeCAD AI: ❌ {provider_name} provider unavailable - missing '{missing_sub_dependency}' sub-dependency\n"
                )
                FreeCAD.Console.PrintWarning(
                    f"FreeCAD AI: This is a sub-dependency of '{missing_dependency}' that wasn't installed properly\n"
                )
            else:
                FreeCAD.Console.PrintWarning(
                    f"FreeCAD AI: ❌ {provider_name} provider unavailable - missing '{missing_dependency}' dependency\n"
                )

            # Attempt automatic installation with sub-dependency handling
            if not _dependency_install_attempted:
                if missing_sub_dependency:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Attempting to install {missing_dependency} with sub-dependencies...\n"
                    )
                else:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Attempting to install {missing_dependency} automatically...\n"
                    )

                if _attempt_dependency_installation():
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: ✅ Dependencies installed - restart FreeCAD to use {provider_name}\n"
                    )
                else:
                    FreeCAD.Console.PrintWarning(
                        f"FreeCAD AI: ❌ Automatic installation failed\n"
                    )
                    if missing_sub_dependency:
                        _show_sub_dependency_guidance(
                            missing_dependency, missing_sub_dependency, provider_name
                        )
                    else:
                        _show_dependency_guidance(missing_dependency, provider_name)
            else:
                if missing_sub_dependency:
                    _show_sub_dependency_guidance(
                        missing_dependency, missing_sub_dependency, provider_name
                    )
                else:
                    _show_dependency_guidance(missing_dependency, provider_name)
        else:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: ❌ {provider_name} provider import failed: {error_msg}\n"
            )

        return None

    except Exception as e:
        error_msg = f"Error loading {provider_name}: {str(e)}"
        _provider_errors[provider_name] = error_msg
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: ❌ {provider_name} provider error: {error_msg}\n"
        )
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: {provider_name} traceback: {traceback.format_exc()}\n"
        )
        return None


def get_claude_provider():
    """Get Claude provider class with lazy loading and dependency management."""
    return _lazy_import_provider("Claude", "claude_provider", "ClaudeProvider")


def get_gemini_provider():
    """Get Gemini provider class with lazy loading and dependency management."""
    return _lazy_import_provider("Gemini", "gemini_provider", "GeminiProvider")


def get_vertexai_provider():
    """Get Vertex AI provider class with lazy loading and dependency management."""
    return _lazy_import_provider("VertexAI", "vertexai_provider", "VertexAIProvider")


def get_openrouter_provider():
    """Get OpenRouter provider class with lazy loading and dependency management."""
    return _lazy_import_provider(
        "OpenRouter", "openrouter_provider", "OpenRouterProvider"
    )


def get_available_providers() -> Dict[str, Any]:
    """Get all available provider classes.

    Returns:
        Dictionary mapping provider names to classes (None if unavailable)
    """
    providers = {
        "Claude": get_claude_provider(),
        "Gemini": get_gemini_provider(),
        "VertexAI": get_vertexai_provider(),
        "OpenRouter": get_openrouter_provider(),
    }

    # Enhanced availability summary with sub-dependency information
    available_count = sum(1 for p in providers.values() if p is not None)
    total_count = len(providers)

    if available_count == 0:
        FreeCAD.Console.PrintWarning(
            f"FreeCAD AI: ⚠️ No AI providers available ({available_count}/{total_count})\n"
        )
        FreeCAD.Console.PrintWarning(
            "FreeCAD AI: Install missing dependencies to enable AI providers\n"
        )

        # Check if it's a sub-dependency issue
        try:
            from utils.dependency_manager import DependencyManager

            manager = DependencyManager()

            if manager.check_dependency("aiohttp"):
                sub_deps = manager.check_sub_dependencies("aiohttp")
                missing_sub_deps = [
                    dep for dep, available in sub_deps.items() if not available
                ]

                if missing_sub_deps:
                    FreeCAD.Console.PrintWarning(
                        f"FreeCAD AI: ⚠️ aiohttp is installed but missing sub-dependencies: {', '.join(missing_sub_deps)}\n"
                    )
                    FreeCAD.Console.PrintWarning(
                        "FreeCAD AI: Use Dependencies tab to fix sub-dependency issues\n"
                    )
        except (ImportError, AttributeError):
            # ImportError: Missing dependency modules for checking
            # AttributeError: Missing expected dependency attributes
            pass  # Ignore errors in sub-dependency checking

    elif available_count < total_count:
        FreeCAD.Console.PrintMessage(
            f"FreeCAD AI: ⚠️ Partial AI provider availability ({available_count}/{total_count})\n"
        )

        # Show which providers are missing and why
        for provider_name, provider_class in providers.items():
            if provider_class is None and provider_name in _provider_errors:
                error = _provider_errors[provider_name]
                if "multidict" in error or "yarl" in error or "aiosignal" in error:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: ⚠️ {provider_name}: Missing sub-dependency\n"
                    )
                else:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: ⚠️ {provider_name}: Missing main dependency\n"
                    )
    else:
        FreeCAD.Console.PrintMessage(
            f"FreeCAD AI: ✅ All AI providers available ({available_count}/{total_count})\n"
        )

    return providers


def get_provider_errors() -> Dict[str, str]:
    """Get any provider loading errors.

    Returns:
        Dictionary mapping provider names to error messages
    """
    return _provider_errors.copy()


def check_dependencies() -> Dict[str, bool]:
    """Check if dependencies are available for providers with enhanced reporting.

    Returns:
        Dictionary mapping dependency names to availability
    """
    dependencies = {}

    try:
        # Try to use the enhanced dependency manager

        from utils.dependency_manager import check_dependencies as enhanced_check

        dependencies = enhanced_check()

        # Log dependency status
        FreeCAD.Console.PrintMessage("FreeCAD AI: Dependency Status:\n")
        for dep_name, available in dependencies.items():
            status = "✅" if available else "❌"
            FreeCAD.Console.PrintMessage(
                f"  {status} {dep_name}: {'Available' if available else 'Missing'}\n"
            )

        return dependencies

    except ImportError:
        FreeCAD.Console.PrintMessage("FreeCAD AI: Using fallback dependency check\n")

        # Fallback manual check
        test_dependencies = ["aiohttp", "requests", "mcp"]

        for dep_name in test_dependencies:
            try:
                __import__(dep_name)
                dependencies[dep_name] = True
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: ✅ {dep_name}: Available\n")
            except ImportError:
                dependencies[dep_name] = False
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: ❌ {dep_name}: Missing\n")

        return dependencies


def install_missing_dependencies():
    """Attempt to install missing dependencies with user guidance."""
    try:
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Checking and installing missing dependencies...\n"
        )

        # Try to use the dependency manager

        from utils.dependency_manager import auto_install_dependencies

        def progress_callback(message):
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: {message}\n")

        success = auto_install_dependencies(progress_callback)

        if success:
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: ✅ Dependencies installed successfully\n"
            )
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: 🔄 Please restart FreeCAD to use the new dependencies\n"
            )
            return True
        else:
            FreeCAD.Console.PrintWarning(
                "FreeCAD AI: ❌ Some dependencies failed to install\n"
            )
            FreeCAD.Console.PrintWarning(
                "FreeCAD AI: See the installation guide above for manual installation\n"
            )
            return False

    except ImportError as e:
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: Could not import dependency manager: {e}\n"
        )
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Please install dependencies manually\n"
        )
        return False
    except (subprocess.CalledProcessError, PermissionError, FileNotFoundError) as e:
        # subprocess.CalledProcessError: Installation command failed
        # PermissionError: Insufficient permissions for installation
        # FileNotFoundError: pip or python executable not found
        FreeCAD.Console.PrintError(f"FreeCAD AI: Dependency installation error: {e}\n")
        return False


# For backward compatibility, try to import providers directly
# but don't fail if dependencies are missing
ClaudeProvider = get_claude_provider()
GeminiProvider = get_gemini_provider()
VertexAIProvider = get_vertexai_provider()
OpenRouterProvider = get_openrouter_provider()

# Import MCP integrated provider directly (it has no external dependencies)
try:
    from ai.providers.mcp_integrated_provider import MCPIntegratedProvider

    FreeCAD.Console.PrintMessage(
        "FreeCAD AI: ✅ MCPIntegratedProvider loaded successfully\n"
    )
except ImportError as e:
    FreeCAD.Console.PrintWarning(
        f"FreeCAD AI: ❌ Failed to import MCPIntegratedProvider: {e}\n"
    )
    MCPIntegratedProvider = None

# Export list for explicit imports
__all__ = [
    "BaseAIProvider",
    "AIResponse",
    "AIMessage",
    "MessageRole",
    "get_claude_provider",
    "get_gemini_provider",
    "get_vertexai_provider",
    "get_openrouter_provider",
    "get_available_providers",
    "get_provider_errors",
    "check_dependencies",
    "install_missing_dependencies",
    "MCPIntegratedProvider",
]

# Add provider classes if they loaded successfully
if ClaudeProvider:
    __all__.append("ClaudeProvider")
if GeminiProvider:
    __all__.append("GeminiProvider")
if OpenRouterProvider:
    __all__.append("OpenRouterProvider")

# Show initial status
try:
    available_providers = get_available_providers()
    dependency_status = check_dependencies()

    # Show summary
    provider_count = sum(1 for p in available_providers.values() if p is not None)
    dependency_count = sum(1 for d in dependency_status.values() if d)

    if provider_count == 0:
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: 💡 To enable AI providers, install missing dependencies using the Dependencies tab\n"
        )

except (ImportError, AttributeError, NameError) as e:
    # ImportError: Missing modules during provider initialization
    # AttributeError: Missing expected provider attributes
    # NameError: Missing variables during initialization
    FreeCAD.Console.PrintError(
        f"FreeCAD AI: Error during provider initialization: {e}\n"
    )
