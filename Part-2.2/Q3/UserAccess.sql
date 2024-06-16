ALTER TABLE Users MODIFY COLUMN UserId INT AUTO_INCREMENT PRIMARY KEY;
ALTER TABLE RoleAssignments MODIFY COLUMN RoleAssignmentID INT AUTO_INCREMENT PRIMARY KEY;

-- Creating table to handle Role Exceptions 
CREATE TABLE IF NOT EXISTS RoleExceptions (
    ExceptionID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(100) NOT NULL,
    RoleID INT NOT NULL,
    ExpirationDate DATE
);

DELIMITER //

CREATE PROCEDURE ManageUserAccess (
    IN p_DisplayName VARCHAR(100),
    IN p_Email VARCHAR(100),
    IN p_JobTitle VARCHAR(100)
)
BEGIN
    DECLARE v_RoleID INT;
    DECLARE v_UserId INT;
    DECLARE v_ExistingDisplayName VARCHAR(100);
    DECLARE v_ExistingJobTitle VARCHAR(100);
    DECLARE v_ExceptionRoleID INT;

    -- Determine the role ID based on JobTitle
    IF p_JobTitle LIKE '%Cafeteria Manager%' OR p_JobTitle LIKE '%Cafeteria Assistant Manager%' THEN
        SET v_RoleID = (SELECT RoleID FROM Roles WHERE RoleName = 'Cafeteria Manager' LIMIT 1);
    ELSEIF p_JobTitle LIKE '%Regional Manager%' THEN
        SET v_RoleID = (SELECT RoleID FROM Roles WHERE RoleName = 'Support Cafeteria Manager' LIMIT 1);
    ELSEIF p_JobTitle LIKE '%Special Diet Manager%' THEN
        SET v_RoleID = (SELECT RoleID FROM Roles WHERE RoleName = 'Agent' LIMIT 1);
    ELSE
        SET v_RoleID = (SELECT RoleID FROM Roles WHERE RoleName = 'No Access' LIMIT 1);
    END IF;

    -- reole exceptions
    SELECT RoleID INTO v_ExceptionRoleID
    FROM RoleAssignments
    WHERE UserID = (SELECT UserId FROM Users WHERE Email = p_Email LIMIT 1)
      AND RoleID IN (SELECT RoleID FROM Roles WHERE RoleName = 'Agent');

    -- If there is an exception, use the exception role ID
    IF v_ExceptionRoleID IS NOT NULL THEN
        SET v_RoleID = v_ExceptionRoleID;
    END IF;

    -- Does user already exists
    SELECT UserId, DisplayName, JobTitle INTO v_UserId, v_ExistingDisplayName, v_ExistingJobTitle
    FROM Users
    WHERE Email = p_Email
    LIMIT 1;

    -- If user exists, update Display Name and Job Title 
    IF v_UserId IS NOT NULL THEN
        IF p_DisplayName != v_ExistingDisplayName THEN
            UPDATE Users
            SET DisplayName = p_DisplayName, ModifiedOn = DATE_FORMAT(NOW(), '%H:%i:%s.%f')
            WHERE UserId = v_UserId;
        END IF;

        IF p_JobTitle != v_ExistingJobTitle THEN
            UPDATE Users
            SET JobTitle = p_JobTitle, ModifiedOn = DATE_FORMAT(NOW(), '%H:%i:%s.%f')
            WHERE UserId = v_UserId;
        END IF;

        -- Update RoleAssignment if needed
        IF (SELECT RoleID FROM RoleAssignments WHERE UserID = v_UserId LIMIT 1) != v_RoleID THEN
            UPDATE RoleAssignments
            SET RoleID = v_RoleID
            WHERE UserID = v_UserId;
        END IF;
    ELSE
        -- If user doesn't exist, insert new 
        INSERT INTO Users (DisplayName, Email, JobTitle, ModifiedOn)
        VALUES (p_DisplayName, p_Email, p_JobTitle, DATE_FORMAT(NOW(), '%H:%i:%s.%f'));

        -- Get the new UserId
        SET v_UserId = LAST_INSERT_ID();

        -- Insert the role assignment
        INSERT INTO RoleAssignments (RoleID, UserID)
        VALUES (v_RoleID, v_UserId);
    END IF;
END //

DELIMITER ;


