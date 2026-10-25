def allowed(age):
    # Намеренная неисправность. Сохраните строгий тип и исправьте границу.
    return type(age) is int and 14 < age <= 80
