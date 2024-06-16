-- Test 1: Add a new Cafeteria Manager
CALL ManageUserAccess('Daniella Thompson', 'daniellathompson@example.com', 'Cafeteria Manager');

-- Verify 
SELECT * FROM Users WHERE Email = 'daniellathompson@example.com';
SELECT * FROM RoleAssignments WHERE UserID = (SELECT UserId FROM Users WHERE Email = 'daniellathompson@example.com');


-- Test 2: Update existing user's Display Name
CALL ManageUserAccess('Daniella Thompson Updated', 'daniellathompson@example.com', 'Cafeteria Manager');

-- Verify
SELECT * FROM Users WHERE Email = 'daniellathompson@example.com';

-- Test 3: Update existing user's Job Title and Role
CALL ManageUserAccess('Daniella Thompson Updated', 'daniellathompson@example.com', 'Special Diet Manager');

-- Verify the update
SELECT * FROM Users WHERE Email = 'daniellathompson@example.com';
SELECT * FROM RoleAssignments WHERE UserID = (SELECT UserId FROM Users WHERE Email = 'daniellathompson@example.com');

-- Test 4: Role exception
INSERT INTO RoleExceptions (Email, RoleID, ExpirationDate) VALUES ('daniellathompson@example.com', 2, '2025-01-01');
CALL ManageUserAccess('Daniella Thompson Updated', 'daniellathompson@example.com', 'Regional Manager');

-- Verify 
SELECT * FROM RoleAssignments WHERE UserID = (SELECT UserId FROM Users WHERE Email = 'janesmith@example.com');
SELECT * FROM RoleExceptions WHERE Email = 'janesmith@example.com';


