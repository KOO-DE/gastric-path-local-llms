SELECT
    DISTINCT 환자번호,
    원무접수ID,
    검사시행일,
    Differentiation,
    Diff_Num,
    CASE
        WHEN (CHAR_LENGTH(Differentiation) - CHAR_LENGTH(REPLACE (Differentiation, '%%', ''))) = 2
        THEN (CASE
            WHEN INSTR(
                TRIM(
                    TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                    FROM Differentiation
                ), 'poorly'
            )
            THEN 'poorly'
            WHEN INSTR(
                TRIM(
                    TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                    FROM Differentiation
                ), 'moderately'
            )
            THEN 'moderately'
            WHEN INSTR(
                TRIM(
                    TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                    FROM Differentiation
                ), 'well'
            )
            THEN 'well'
            END
        )
        WHEN (Diff_Num = 2 AND NULLIF(Test, '') IS NULL)
        THEN (CASE
            WHEN INSTR(
                SUBSTR(
                    Differentiation, INSTR(Differentiation, 'to')
                ), 'poorly'
            )
            THEN 'poorly'
            WHEN INSTR(
                SUBSTR(
                    Differentiation, INSTR(Differentiation, 'to')
                ), 'moderately'
            ) != 0
            THEN 'moderately'
            END
        )
        WHEN (Diff_Num = 2 AND NULLIF(Test, '') IS NOT NULL)
        THEN (CASE
            WHEN (100 - Test) > Test
            THEN (CASE
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                        FROM Differentiation
                    ),'poorly'
                ) != 0
                THEN 'poorly'
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                        FROM Differentiation
                    ), 'moderately '
                ) != 0
                THEN 'moderately'
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiation, INSTR(Differentiation, 'to'))
                        FROM Differentiation
                    ), 'well'
                )
                THEN 'well'
                END
            )
            WHEN (100 - Test) <= Test
            THEN (CASE
                    WHEN INSTR(SUBSTR(Differentiation, INSTR(Differentiation, 'to')), 'poorly') != 0
                    THEN 'poorly'
                    WHEN INSTR(SUBSTR(Differentiation, INSTR(Differentiation, 'to')), 'moderately') != 0
                    THEN 'moderately'
                    WHEN INSTR(SUBSTR(Differentiation, INSTR(Differentiation, 'to')), 'well') != 0
                    THEN 'well'
                END
            )
            END
        )
        WHEN (Diff_Num = 2 AND Differentiated IS NOT NULL)
        THEN (CASE
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiated, INSTR(Differentiated, 'to'))
                        FROM Differentiated
                    ), 'poorly'
                ) != 0
                THEN 'poorly'
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiated,INSTR(Differentiated, 'to'))
                        FROM Differentiated
                    ),'moderately'
                ) != 0
                THEN 'moderately'
                WHEN INSTR(
                    TRIM(
                        TRAILING SUBSTR(Differentiated, INSTR(Differentiated, 'to'))
                        FROM Differentiated
                    ), 'well'
                ) != 0
                THEN 'well'
            END
        )
        ELSE (CASE
                WHEN INSTR(Differentiation, 'poorly') != 0
                THEN 'poorly'
                WHEN INSTR(Differentiation, 'moderately') != 0
                THEN 'moderately'
                WHEN INSTR(Differentiation, 'well') != 0
                THEN 'well'
            END
        )
    END AS Diff_Maj,
    Test AS Diff_P
FROM (
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        CASE
            WHEN (Differentiation IS NOT NULL)
            THEN Differentiation
            WHEN (Differentiated_2 IS NOT NULL)
            THEN Differentiated_2
        END AS Differentiation,
        CASE
            WHEN INSTR(Differentiation, 'to ') != 0
            THEN '2'
            WHEN INSTR(Differentiation, ',') != 0
            THEN '2'
            WHEN INSTR(Differentiation, ' and ') != 0
            THEN '2'
            WHEN (INSTR(Differentiated_2, 'to') != 0 AND (INSTR(Differentiated_2, 'Moderately') != 0 OR INSTR(Differentiated_2, 'Well') != 0 OR INSTR(Differentiated_2, 'Poorly')) != 0)
            THEN '2'
            ELSE '1'
        END AS Diff_Num,
        REPLACE(
            TRIM(
                TRAILING SUBSTR(
                    CASE
                        WHEN INSTR(Test, '%%') = 0
                        THEN ''
                        ELSE Test
                    END, INSTR(Test, '%%')
                )
                FROM Test
            ), '%%', ''
        ) AS Test,
        Differentiated
    FROM (
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            CASE
                WHEN NULLIF(Differentiation, '') IS NULL
                THEN Differentiation_2
                ELSE TRIM(BOTH FROM Differentiation)
            END AS Differentiation,
            Test,
            Differentiated,
            REPLACE(
                REPLACE(
                    REPLACE(
                        CONCAT(
                            Diff_Poo, ',', Diff_Well, ',', Diff_Mod, ',', Diff_To
                        ), '0,', ''
                    ), ',0', ''
                ), '0', ''
            ) AS Differentiated_2
        FROM(
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                Differentiation,
                REPLACE(
                    CASE
                        WHEN (CHAR_LENGTH(Early_Gastric_Cancer) - CHAR_LENGTH(REPLACE(Early_Gastric_Cancer, ')', ''))) >= 1
                        THEN (CASE
                                WHEN ((CHAR_LENGTH(SUBSTRING_INDEX(SUBSTRING_INDEX(Early_Gastric_Cancer, ')', 1), '(', -1)) - CHAR_LENGTH(REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(Early_Gastric_Cancer, ')', 1), '(', -1), 'Differentiated', ''))) >= 1)
                                THEN SUBSTRING_INDEX(
                                        SUBSTRING_INDEX(
                                            SUBSTRING_INDEX(
                                                SUBSTRING_INDEX(Early_Gastric_Cancer, ')', 1), '(', -1
                                            ), ',', 2
                                    ), ',', -1
                                )
                            END
                        ) 
                    END, 'Differentiated', ''
                ) AS Differentiation_2,
                REGEXP_REPLACE(Differentiation, '[^0-9%%]', '') AS Test,
                Differentiated,
                CASE
                    WHEN INSTR(Differentiated, 'poorly') != 0
                    THEN 'Poorly'
                    ELSE 0
                END AS Diff_Poo,
                CASE
                    WHEN INSTR(Differentiated, 'well') != 0
                    THEN 'Well'
                    ELSE 0
                END AS Diff_Well,
                CASE
                    WHEN INSTR(Differentiated, 'moderately') != 0
                    THEN 'Moderately'
                    ELSE 0
                END AS Diff_Mod,
                CASE
                    WHEN INSTR(Differentiated, 'to') != 0
                    THEN 'to'
                    ELSE 0
                END AS Diff_To
            FROM(
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    REGEXP_REPLACE(
                        REPLACE(
                            TRIM(
                                TRAILING SUBSTR(Differentiation, INSTR(Differentiation, '\n'))
                                FROM Differentiation
                            ), 'Differentiation', ''
                        ), '[(|.|;|:]', ''
                    ) AS Differentiation,
                    REGEXP_REPLACE(
                        TRIM(
                            TRAILING SUBSTR(Early_Gastric_Cancer, INSTR(Early_Gastric_Cancer, '\n'))
                            FROM Early_Gastric_Cancer
                        ), '[.|;|:]', ''
                    ) AS Early_Gastric_Cancer,
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(Differentiated, '\n', 4), '\n', -1
                    ) AS Differentiated
                FROM(
                    SELECT
                        원무접수ID,
                        환자번호,
                        검사시행일,
                        SUBSTR(병리진단, INSTR(병리진단, 'Differentiation:')) AS Differentiation,
                        SUBSTR(병리진단, INSTR(병리진단, 'Early gAStric cancer')) AS Early_Gastric_Cancer,
                        CASE
                            WHEN INSTR(병리진단, 'Differentiated') != 0
                            THEN SUBSTRING_INDEX(병리진단, 'Differentiated', 1)
                        END AS Differentiated
                    FROM pathologic_biopsy_03
                ) biopsy
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
