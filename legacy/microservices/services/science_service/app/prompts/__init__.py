try:
    from app.prompts.controller import prompt_controller
except ImportError:
    from services.science_service.app.prompts.controller import prompt_controller
