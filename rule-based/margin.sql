SELECT
    원무접수ID,
    환자번호,
    검사시행일,
    pProx_Margin,
    pDist_Margin,
    CASE
        WHEN (NULLIF(pProx_Margin, '') IS NULL AND NULLIF(pDist_Margin, '') IS NULL)
        THEN 'No'
        WHEN (pProx_Margin IS NOT NULL AND NULLIF(pDist_Margin, '') IS NULL)
        THEN 'No'
        WHEN (NULLIF(pProx_Margin, '') IS NULL AND pDist_Margin IS NOT NULL)
        THEN 'No'
        WHEN (pProx_Margin IS NOT NULL AND pDist_Margin IS NOT NULL)
        THEN 'Yes'
    END AS pSafe_Margin
FROM(
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        COALESCE(Proximal, CRM) AS pProx_Margin,
        COALESCE(Distal, CRM) AS pDist_Margin
    FROM(
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            병리진단,
            # Clear Resection Margin
            CASE
                WHEN INSTR(병리진단, 'clear both resection margin') != 0
                THEN 'CRM'
                WHEN INSTR(병리진단, 'clear borh resection margin') != 0
                THEN 'CRM'
                WHEN INSTR(병리진단, 'clcear both resection margin') != 0
                THEN 'CRM'
                WHEN INSTR(병리진단, 'clear resection margin') != 0
                THEN 'CRM'
                WHEN INSTR(병리진단, 'clean both resection margin') != 0
                THEN 'CRM'
                WHEN INSTR(병리진단, 'clear lines of resection') != 0
                THEN 'CRM'
                END AS CRM,
            CASE
                WHEN INSTR(병리진단, 'positive proximal resection margin') != 0
                THEN 'PRM'
                ELSE REGEXP_SUBSTR(
                    NULLIF(
                        SUBSTR(
                            Margin, INSTR(Margin, 'proximal')
                        ), ' '
                    ), '[0-9]+[.]?[0-9]?'
                )
            END AS Proximal,
            CASE
                WHEN INSTR(병리진단, 'positive distal resection margin') != 0
                THEN 'DRM'
                ELSE REGEXP_SUBSTR(
                    NULLIF(
                        SUBSTR(
                            Margin, INSTR(Margin, 'distal')
                        ), ' '
                    ), '[0-9]+[.]?[0-9]?'
                )
            END AS Distal
        FROM(
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                병리진단,
                TRIM(
                    SUBSTR(Margin, INSTR(Margin, '\n'))
                    FROM Margin
                ) AS Margin
            FROM(
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    병리진단,
                    CASE
                        WHEN INSTR(병리진단, 'clear both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'clear both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'clear borh resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단,'clear borh resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'clcear both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'clcear both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'clear resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'clear resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'clean both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'clean both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'clear lines of resection') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'clear lines of resection')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'negative both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'negative both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'negative to both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'negative to both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'negative resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'negative resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'positive both resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단,INSTR(병리진단, 'positive both resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'positive distal resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'positive distal resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'positive proximal resection margin') != 0 
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'positive proximal resection margin')
                            ), ' '
                        )
                        WHEN INSTR(병리진단, 'resection margin') != 0
                        THEN NULLIF(
                            SUBSTR(
                                병리진단, INSTR(병리진단, 'resection margin')
                            ), ' '
                        )
                    END AS Margin
                FROM pathology_report
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
