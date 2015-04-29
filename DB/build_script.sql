--break stuff
DROP TABLE IF EXISTS Players;

--create stuff
CREATE TABLE Players (
  ID INTEGER PRIMARY KEY AUTOINCREMENT,
  FirstName VARCHAR NOT NULL,
  Gil INTEGER NOT NULL
);

--populate stuff
INSERT INTO Players (FirstName, Gil) VALUES ('Steve', 100);

