-- SQLite
-- Attach the secondary database
ATTACH DATABASE 'C:\Users\cheyl\OneDrive\Documents\Git Repos\ultimate-flaggle\src\databases\flaggle2.db' AS secondary;


-- Insert data from the table in the secondary database into the primary database
DELETE FROM GameDetail
WHERE(
    CASE
        WHEN GameDetailId >= 86 AND GameDetailId <= 96 THEN datetime(DateTimeGuessed, '+1 hours')
        ELSE DateTimeGuessed END 
) <= '2025-04-01';

INSERT INTO main.GameDetail (UniqueId, GameId, DateTimeGuessed, Country, Distance, Direction, ComparedImageUrl)
SELECT UniqueId, GameId, DateTimeGuessed, Country, Distance, Direction, ComparedImageUrl FROM secondary.GameDetail
WHERE DATE(DateTimeGuessed) <= '2025-04-01';

-- Verify the data
SELECT * FROM main.GameDetail;

-- Detach the secondary database
DETACH DATABASE secondary;