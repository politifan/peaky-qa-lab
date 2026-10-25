CREATE TABLE owners(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE tickets(id INTEGER PRIMARY KEY, owner_id INTEGER, title TEXT, status TEXT NOT NULL);
INSERT INTO owners VALUES (1,'Учебный Север'),(2,'Учебный Юг');
INSERT INTO tickets VALUES (1,1,'Первая','open'),(2,2,'Вторая','closed'),(3,99,NULL,'open'),(4,1,'','closed');
