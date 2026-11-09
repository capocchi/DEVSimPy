# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# AI_SessionMixin_Example.py --- Example of how to use the AI session mixin.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  07/10/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
#
# GENERAL NOTES AND REMARKS:
# This file demonstrates how to integrate AI session storage into existing
# AI assistant panels without changing their structure.
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

import sys


### Example 1: Basic usage with inheritance ###

class MyAIPanel(wx.Panel, AI_SessionMixin):
    """Example AI panel that inherits from both wx.Panel and AI_SessionMixin.
    
    This demonstrates the mixin pattern - no structural changes to existing code.
    """
    
    def __init__(self, parent, editor_host=None):
        # Initialize parent class first (standard Python MRO)
        super().__init__(parent)
        
        # Then initialize mixin attributes
        self.editor_host = editor_host or parent
        
        # Set model name when available
        if hasattr(editor_host, 'cb') and editor_host.cb:
            self.model_name = editor_host.cb.label
    
    def on_prompt_changed(self, event=None):
        """Handle prompt changes."""
        # Store session automatically when user types
        self.store_session()


### Example 2: Using with existing AIEditorAssistantPanel ###

# Option A: Multiple inheritance (recommended)
class EnhancedAIPanel(AIEditorAssistantPanel, AI_SessionMixin):
    """Enhanced AI panel that adds session storage to existing panel."""
    
    def __init__(self, parent, editor_host=None):
        # Call parent init first
        super().__init__(parent, editor_host)
        
        # Initialize mixin attributes after parent init
        self.model_name = None
        
        # Optionally set model name from host if available
        if hasattr(editor_host, 'cb') and editor_host.cb:
            self.model_name = editor_host.cb.label
    
    def on_prompt_changed(self, event=None):
        """Override to store session when prompt changes."""
        super().on_prompt_changed(event)  # Call parent method
        
        # Store session automatically
        if self.model_name:
            self.store_session()


### Example 3: Manual integration without inheritance ###

# Option B: Manual composition (if you cannot change class hierarchy)
class MyAIPanel(wx.Panel):
    """AI panel with manually added session storage."""
    
    def __init__(self, parent, editor_host=None):
        super().__init__(parent)
        
        self.editor_host = editor_host or parent
        
        # Manually add mixin methods
        from Mixins.AI_SessionMixin import AI_SessionMixin
        for attr in dir(AI_SessionMixin):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(AI_SessionMixin(), attr))
        
        self.model_name = None
    
    def on_prompt_changed(self, event=None):
        """Handle prompt changes."""
        # Store session when user types
        if self.model_name:
            self.store_session()


### Example 4: Complete integration pattern ###

class FullyIntegratedAIPanel(AIEditorAssistantPanel, AI_SessionMixin):
    """Fully integrated AI panel with automatic session management.
    
    This class automatically stores sessions when the model changes
    and provides convenient methods for session management.
    """
    
    def __init__(self, parent, editor_host=None):
        super().__init__(parent, editor_host)
        
        # Set model name from current model if available
        self._set_model_name()
        
        # Bind to model change events
        self.model_choice.Bind(wx.EVT_COMBOBOX, self._on_model_changed)
    
    def _set_model_name(self):
        """Set the model name for session storage."""
        if hasattr(self.editor_host, 'cb') and self.editor_host.cb:
            self.model_name = self.editor_host.cb.label
    
    def _on_model_changed(self, event=None):
        """Handle model selection change."""
        # Update model name
        self._set_model_name()
        
        # Store current session with new model name if exists
        if hasattr(self, '_ask_messages') and self._ask_messages:
            self.store_session()
    
    def on_prompt_changed(self, event=None):
        """Override to store session when prompt changes."""
        super().on_prompt_changed(event)
        
        # Store session automatically
        if self.model_name:
            self.store_session()


### Usage Examples ###

# In your main application code:

def setup_ai_panel_with_sessions(editor_host):
    """Setup AI panel with session storage capabilities."""
    
    from Editor import AIEditorAssistantPanel
    from Mixins.AI_SessionMixin import AI_SessionMixin
    
    # Create enhanced panel
    panel = EnhancedAIPanel(
        parent=editor_host,
        editor_host=editor_host
    )
    
    return panel


def load_saved_session(panel, model_name):
    """Load a previously saved session for a specific model."""
    session = panel.load_session(model_name)
    if session:
        # Restore session data
        if 'prompt' in session:
            panel.prompt_input.SetValue(session['prompt'])
        
        if 'mode' in session:
            panel.mode_choice.SetSelection(session['mode'])
        
        if 'messages' in session:
            panel._ask_messages = session['messages']
    
    return session


def remove_session(panel, model_name):
    """Remove saved session for a specific model."""
    success = panel.remove_session(model_name)
    if success:
        sys.stdout.write(f"Session removed for model: {model_name}\n")
    
    return success


### Integration with existing code ###

# This is how you would integrate it into your existing Editor.py:

class AIEditorAssistantPanelWithSessions(AIEditorAssistantPanel, AI_SessionMixin):
    """AI assistant panel with session storage - drop-in replacement."""
    
    def __init__(self, parent, editor_host=None):
        # Call parent constructor first (preserves all existing functionality)
        super().__init__(parent, editor_host=editor_host)
        
        # Initialize mixin attributes
        self.model_name = None
        
        # Set model name from current model if available
        if hasattr(self.editor_host, 'cb') and self.editor_host.cb:
            self.model_name = self.editor_host.cb.label
    
    def _on_model_changed(self, event=None):
        """Handle model selection change."""
        super()._on_model_changed(event)  # Call parent method
        
        # Update model name
        if hasattr(self.editor_host, 'cb') and self.editor_host.cb:
            self.model_name = self.editor_host.cb.label
        
        # Store session if messages exist
        if hasattr(self, '_ask_messages') and self._ask_messages:
            self.store_session()


### Key Points ###

# 1. No structural changes to existing code - just add mixin inheritance
# 2. Sessions are stored in .amd zip files under 'session/' directory
# 3. Session format is JSON with current panel state
# 4. Automatic storage on model change or prompt update
# 5. Fallback to temp directory if MAIN_WINDOW not available

### Session File Structure ###

# Inside .amd file:
#   session/
#     MyModel.json    <- Session data for "MyModel" atomic model

# Session JSON format:
# {
#     "mode": 0,              # 0=Ask, 1=Build
#     "prompt": "...",        # Current prompt text
#     "messages": [...],      # Conversation history
#     "context_signature": null  # Context signature if applicable
# }
