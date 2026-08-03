SELECT
    DISTINCT 원무접수ID,
    환자번호,
    검사시행일,
    REPLACE(
        REPLACE(
            REPLACE(
                CONCAT(
                    INTESTINAL, ',', Diffuse, ',', `Mixed`, ',', Lauren_Type_None
                ), '0,', ''
            ), ',0', ''
        ), '0', ''
    ) AS Lauren_Type
FROM(
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        CASE 
            WHEN INSTR(Lauren_Type, 'intestinal') != 0
            THEN 'Intestinal'
            WHEN INSTR(Lauren_Type, 'intestinal ed') != 0
            THEN 'Intestinal'
            WHEN INSTR(Lauren_Type, 'intestinal ype') != 0
            THEN 'Intestinal'
            ELSE 0
        END AS Intestinal,
        CASE 
            WHEN INSTR(Lauren_Type, 'diffuse') != 0
            THEN 'diffuse'
            ELSE 0
        END AS Diffuse,
        CASE 
            WHEN INSTR(Lauren_Type, 'mixed') != 0
            THEN 'Mixed'
            ELSE 0
        END AS `Mixed`,
        CASE 
            WHEN nullif(Lauren_Type, '') IS NULL
            THEN 'None'
            ELSE 0
        END AS Lauren_Type_None
    FROM(
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            CASE 
                WHEN NULLIF(Lauren_Classification, '') IS NULL
                THEN Lauren_Type_2
                ELSE REPLACE(Lauren_Classification, 'type', '')
            END AS Lauren_Type
        FROM(
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                Lauren_Classification,
                REPLACE(
                    CASE
                        WHEN (CHAR_LENGTH(Early_Gastric_Cancer) - CHAR_LENGTH(REPLACE(Early_Gastric_Cancer, ')', ''))) >= 2
                        THEN (
                            CASE
                                WHEN (
                                    CHAR_LENGTH(
                                        SUBSTRING_INDEX(
                                            SUBSTRING_INDEX(
                                                Early_Gastric_Cancer, ')', 2
                                            ), '(', -1
                                        )
                                    ) - CHAR_LENGTH(
                                        REPLACE(
                                            SUBSTRING_INDEX(
                                                SUBSTRING_INDEX(
                                                    Early_Gastric_Cancer, ')', 2
                                                ), '(', -1
                                            ), 'type', ''
                                        )
                                    )
                                ) >= 1
                                THEN SUBSTRING_INDEX(
                                    SUBSTRING_INDEX(
                                        Early_Gastric_Cancer, ')', 2
                                    ), '(', -2
                                )
                            END
                        )
                    END, 'type', ''
                ) AS Lauren_Type_2
            FROM(
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    육안소견,
                    REGEXP_REPLACE(
                        REPLACE(
                            TRIM(
                                TRAILING SUBSTR(Lauren_Classification, INSTR(Lauren_Classification, '\n'))
                                FROM Lauren_Classification
                            ), 'Lauren classification:', ''
                        ), '[(|.|;|:]', ''
                    ) AS Lauren_Classification,
                    REGEXP_REPLACE(
                        TRIM(
                            TRAILING SUBSTR(Early_Gastric_Cancer, INSTR(Early_Gastric_Cancer, '\n'))
                            FROM Early_Gastric_Cancer
                        ), '[.|;|:]', ''
                    ) AS Early_Gastric_Cancer
                FROM(
                    SELECT
                        원무접수ID,
                        환자번호,
                        검사시행일,
                        병리진단,
                        육안소견,
                        SUBSTR(병리진단, INSTR(병리진단, 'Lauren classification')) AS Lauren_Classification,
                        SUBSTR(병리진단, INSTR(병리진단, 'Early gastric cancer')) AS Early_Gastric_Cancer
                    FROM(
                        SELECT * FROM pathologic_biopsy_03
                    ) biopsy
                ) biopsy
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
