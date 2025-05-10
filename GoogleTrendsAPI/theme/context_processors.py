def theme_settings(request):
    """
    Context processor for theme settings.
    Returns theme-related context variables.
    """
    # Default theme - can be changed to any of your theme files
    theme = request.session.get('theme', 'dark')  # Default to dark theme

    return {
        'ACTIVE_THEME': theme,
        'THEME_CSS': f'css/{theme}-theme.css'  # Points to files in static/css/
    }