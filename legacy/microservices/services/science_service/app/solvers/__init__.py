try:
    from app.solvers.physics import solve_physics
    from app.solvers.chemistry import solve_chemistry
    from app.solvers.biology import solve_biology
except ImportError:
    from services.science_service.app.solvers.physics import solve_physics
    from services.science_service.app.solvers.chemistry import solve_chemistry
    from services.science_service.app.solvers.biology import solve_biology
