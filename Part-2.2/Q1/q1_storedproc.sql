
DELIMITER //

CREATE PROCEDURE GetSalesData (
    IN inputRegion VARCHAR(10),
    IN inputStartDate DATE,
    IN inputEndDate DATE
)
BEGIN
    IF inputStartDate IS NULL OR inputEndDate IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Both StartDate and EndDate are required';
    END IF;

    -- Main query
    SELECT * FROM (
	
        SELECT 
            b.BulkSaleId AS SaleId,
            s.Campus AS Campus,
            CASE 
                WHEN m.Description LIKE 'AC%' THEN 'Academy'
                WHEN m.Description LIKE 'CP%' THEN 'College Preparatory'
                ELSE 'Unknown'
            END AS Site,
            r.ShortName AS Region,
            st.State AS State,
            b.TransactionDate AS SaleDate,
            mt.Description AS MealType,
            m.Description AS MenuItem,
            bs.MealCount AS FreeCount,
            0 AS ReducedCount,
            0 AS PaidCount,
            bs.MealCount AS TotalMealCount,
            'Bulk' AS EntryMethod
        FROM BulkSales b
        JOIN Schools s ON b.SchoolId = s.SchoolId
        JOIN Regions r ON s.RegionId = r.RegionId
        JOIN States st ON r.StateId = st.StateId
        JOIN MealType mt ON b.MealTypeId = mt.MealTypeId
        JOIN MenuItem m ON b.MenuItemId = m.MenuItemId
        JOIN BulkSummarySales bs ON b.BulkSaleId = bs.BulkSaleId
        WHERE m.IsReimbursable = 1
          AND bs.PriceTypeId IN (SELECT PriceTypeId FROM PriceType WHERE PriceTypeCategoryCd = 'STUDENT')
          AND b.TransactionDate BETWEEN inputStartDate AND inputEndDate
          AND (r.ShortName = inputRegion OR inputRegion IS NULL)
        UNION ALL
        
        SELECT 
            ps.PersonSaleId AS SaleId,
            s.Campus AS Campus,
            CASE 
                WHEN g.GradeCd IN ('K', '1', '2', '3', '4', '5') THEN 'Academy'
                WHEN g.GradeCd IN ('6', '7', '8', '9', '10', '11', '12') THEN 'College Preparatory'
                ELSE 'Unknown'
            END AS Site,
            r.ShortName AS Region,
            st.State AS State,
            ps.SaleDate AS SaleDate,
            mt.Description AS MealType,
            m.Description AS MenuItem,
            SUM(CASE WHEN psd.IsMeal = 1 THEN psd.SaleCount ELSE 0 END) AS FreeCount,
            SUM(CASE WHEN psd.IsMeal = 2 THEN psd.SaleCount ELSE 0 END) AS ReducedCount,
            SUM(CASE WHEN psd.IsMeal = 3 THEN psd.SaleCount ELSE 0 END) AS PaidCount,
            SUM(psd.SaleCount) AS TotalMealCount,
            'Person' AS EntryMethod
        FROM PersonSales ps
        JOIN PersonSalesDetail psd ON ps.PersonSaleId = psd.PersonSaleId
        JOIN Schools s ON ps.BuyerSchoolId = s.SchoolId
        JOIN Regions r ON s.RegionId = r.RegionId
        JOIN States st ON r.StateId = st.StateId
        JOIN Grade g ON ps.BuyerGradeId = g.GradeId
        JOIN MealType mt ON psd.MealTypeId = mt.MealTypeId
        JOIN MenuItem m ON psd.MenuItemId = m.MenuItemId
        WHERE m.IsReimbursable = 1
          AND psd.PriceTypeId IN (SELECT PriceTypeId FROM PriceType WHERE PriceTypeCategoryCd = 'STUDENT')
          AND psd.SaleCount != -1
          AND ps.SaleDate BETWEEN inputStartDate AND inputEndDate
          AND (r.ShortName = inputRegion OR inputRegion IS NULL)
        GROUP BY ps.PersonSaleId, s.Campus, Site, r.ShortName, st.State, ps.SaleDate, mt.Description, m.Description
    ) AS CombinedSales;
END //

DELIMITER ;

-- Test Func. Calls...added csv results to folder
CALL GetSalesData('URGV', '2024-04-17', '2024-04-19');

-- Test with start date and end date only...added csv results to folder
CALL GetSalesData(NULL, '2024-04-17', '2024-04-19');

-- Test with Start Date only
CALL GetSalesData(NULL, '2024-04-17', NULL);
