SELECT
    원무접수ID,
    환자번호,
    검사시행일,
    Site_Num,
    NULLIF(
        REPLACE(
            REPLACE(
                REPLACE(
                    CONCAT(
                        Cardia, ',', Fundus, ',', Upper_Body, ',', Mid_Body, ',', Lower_Body, ',', `Body`, ',', Pylorus, ',', Antrum
                    ), '0,', '' 
                ), ',0', ''
            ), '0', ''
        ), ''
    ) AS Tumor_Location,
    NULLIF(
        REPLACE(
            REPLACE(
                REPLACE(
                    CONCAT(
                        Anterior, ',', Posterior, ',', Greater, ',', Lesser, ',', Anastomosis_Site
                    ), '0,', ''
                ), ',0', ''
            ), '0', ''
        ), ''
    ) AS Tumor_Circumference,
    CASE
        WHEN (NULLIF(Cardia, '0') IS NULL AND NULLIF(Fundus, '0') IS NULL AND NULLIF(Upper_Body, '0') IS NULL AND NULLIF(Mid_Body, '0') IS NULL AND NULLIF(Lower_Body, '0') IS NULL AND NULLIF(Pylorus, '0') IS NULL AND NULLIF(Antrum, '0') IS NULL AND NULLIF(Anterior, '0') IS NULL AND NULLIF(Posterior, '0') IS NULL AND NULLIF(Greater, '0') IS NULL AND NULLIF(Lesser, '0') IS NULL AND NULLIF(Anastomosis_Site, '0') IS NULL AND NULLIF(`Body`, '0') IS NULL AND Site_Path IS NOT NULL)
        THEN Site_Path
    END AS Location_etc,
    CASE
        WHEN (NULLIF(Cardia, '0') IS NULL AND NULLIF(Fundus, '0') IS NULL AND NULLIF(Upper_Body, '0') IS NULL AND NULLIF(Mid_Body, '0') IS NULL AND NULLIF(Lower_Body, '0') IS NULL AND NULLIF(Pylorus, '0') IS NULL AND NULLIF(Antrum, '0') IS NULL AND NULLIF(Anterior, '0') IS NULL AND NULLIF(Posterior, '0') IS NULL AND NULLIF(Greater, '0') IS NULL AND NULLIF(Lesser, '0') IS NULL AND NULLIF(Anastomosis_Site, '0') IS NULL AND NULLIF(`Body`, '0') IS NULL)
        THEN 병리진단
    END AS Undecided
FROM(
    SELECT *,
        CASE
            WHEN (NULLIF(Upper_Body, '0') IS NULL AND NULLIF(Mid_Body, '0') IS NULL AND NULLIF(Lower_Body, '0') IS NULL AND INSTR(Site_Path, 'body') != 0)
            THEN 'Body'
            ELSE 0
        END AS `Body`
    FROM(
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            육안소견,
            병리진단,
            Site_Num,
            Site_Path,
            CASE
                WHEN INSTR(Site_Path, 'cardia') != 0
                THEN 'Cardia'
                WHEN INSTR(Site_Path, 'carida') != 0
                THEN 'Cardia'
                WHEN INSTR(Site_Path, 'cardiac region') != 0 
                THEN 'Cardia'
                WHEN (INSTR(Site_Path, 'esophagogastric') != 0 AND INSTR(Site_Path, 'junction') != 0)
                THEN 'Cardia'
                WHEN (INSTR(Site_Path, 'esophagogastic') != 0 AND INSTR(Site_Path, 'junction') != 0)
                THEN 'Cardia'
                WHEN (INSTR(Site_Path, 'gastroesophageal') != 0 AND INSTR(Site_Path, 'junction') != 0)
                THEN 'Cardia'
                WHEN (INSTR(Site_Path, 'EG') != 0 AND INSTR(Site_Path, 'junction') != 0)
                THEN 'Cardia'
                WHEN (INSTR(Site_Path, 'E-G') != 0 AND INSTR(Site_Path, 'junction') != 0)
                THEN 'Cardia'
                WHEN INSTR(Site_Path, 'EGJ') != 0
                THEN 'Cardia'
                ELSE 0
            END AS Cardia,
            CASE
                WHEN INSTR(Site_Path, 'fundus') != 0
                THEN 'Fundus'
                ELSE 0
            END AS Fundus,
            CASE
                WHEN INSTR(Site_Path, 'upper body') != 0
                THEN 'Upper body'
                WHEN INSTR(Site_Path, 'upperbody') != 0
                THEN 'Upper body'
                WHEN INSTR(Site_Path, 'high body') != 0
                THEN 'Upper body'
                WHEN (INSTR(Site_Path, 'upper') != 0 AND INSTR(Site_Path, 'body') != 0)
                THEN 'Upper body'
                WHEN (INSTR(Site_Path, 'upper') != 0 AND INSTR(Site_Path, 'dody') != 0)
                THEN 'Upper body'
                ELSE 0
            END AS Upper_Body,
            CASE
                WHEN INSTR(Site_Path, 'mid body') != 0
                THEN 'Mid body'
                WHEN INSTR(Site_Path, 'midbody') != 0
                THEN 'Mid body'
                WHEN INSTR(Site_Path, 'mid-body') != 0
                THEN 'Mid body'
                WHEN INSTR(Site_Path, 'middle body') != 0
                THEN 'Mid body'
                WHEN INSTR(Site_Path, 'midd body') != 0
                THEN 'Mid body'
                WHEN INSTR(Site_Path, 'midy body') != 0
                THEN 'Mid body'
                WHEN (INSTR(Site_Path, 'mild') != 0 AND INSTR(Site_Path, 'body') != 0)
                THEN 'Mid body'
                WHEN (INSTR(Site_Path, 'mid') != 0 AND INSTR(Site_Path, 'body') != 0)
                THEN 'Mid body'
                WHEN (INSTR(Site_Path, 'middle') != 0 AND INSTR(Site_Path, 'dody') != 0)
                THEN 'Mid body'
                ELSE 0
            END AS Mid_Body,
            CASE
                WHEN INSTR(Site_Path, 'lower body') != 0
                THEN 'Lower body'
                WHEN INSTR(Site_Path, 'lowerbody') != 0
                THEN 'Lower body'
                WHEN INSTR(Site_Path, 'lower-body') != 0
                THEN 'Lower body'
                WHEN INSTR(Site_Path, 'low body') != 0
                THEN 'Lower body'
                WHEN (INSTR(Site_Path, 'lower') != 0 AND INSTR(Site_Path, 'body') != 0 )
                THEN 'Lower body'
                ELSE 0
            END AS Lower_Body,
            CASE
                WHEN INSTR(Site_Path, 'pylorus') != 0
                THEN 'Pylorus'
                WHEN INSTR(Site_Path, 'prepyrolic') != 0
                THEN 'Pylorus'
                WHEN INSTR(Site_Path, 'pyloric area') != 0
                THEN 'Pylorus'
                WHEN INSTR(Site_Path, 'pyloric ring') != 0
                THEN 'Pylorus'
                ELSE 0
            END AS Pylorus,
            CASE
                WHEN INSTR(Site_Path, 'pyloric antrum') != 0
                THEN 'Pyloric antrum'
                WHEN INSTR(Site_Path, 'pyloric antru') != 0
                THEN 'Pyloric antrum'
                WHEN INSTR(Site_Path, 'antrum') != 0
                THEN'Antrum'
                WHEN INSTR(Site_Path, 'angle') != 0
                THEN 'Antrum'
                ELSE 0
            END AS Antrum,
            CASE
                WHEN INSTR(Site_Path, 'anterior') != 0
                THEN 'Anterior wall'
                ELSE 0
            END AS Anterior,
            CASE
                WHEN INSTR(Site_Path, 'posterior') != 0
                THEN 'Posterior wall'
                WHEN INSTR(Site_Path, 'posterir') != 0
                THEN 'Posterior wall'
                ELSE 0
            END AS Posterior,
            CASE
                WHEN INSTR(Site_Path, 'greater') != 0
                THEN 'Greater curvature'
                ELSE 0
            END AS Greater,
            CASE
                WHEN INSTR(Site_Path, 'lesser') != 0
                THEN 'Lesser curvature'
                ELSE 0
            END AS Lesser,
            CASE
                WHEN INSTR(Site_Path, 'anastomosis site') != 0
                THEN 'Anastomosis site'
                WHEN INSTR(Site_Path, 'anastomosis') != 0
                THEN 'Anastomosis site'
                ELSE 0
            END AS Anastomosis_Site
        FROM pathology_report
    ) a
) a
