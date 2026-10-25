def reserve(free,requested):
    # Намеренная неисправность: исследуйте положительность и равенство.
    return free-requested if requested<free else free
