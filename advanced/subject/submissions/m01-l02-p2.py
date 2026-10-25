# Teardown после исключения
# Проверьте target.resources(log) as resources при ValueError внутри with. Ожидаются open:db/open:client и обратные close:client/close:db. После выхода resources.client.is_closed=True; SELECT 1 через resources.db вызывает sqlite3.ProgrammingError.
# Write executable Python tests here.
