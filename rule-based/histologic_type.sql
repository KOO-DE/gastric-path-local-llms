WITH step1 AS (
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                REPLACE(
                                                    REPLACE(
                                                        REPLACE(
                                                            REPLACE(
                                                                REPLACE(
                                                                    REPLACE(
                                                                        REPLACE(
                                                                            REPLACE(
                                                                                REPLACE(
                                                                                    REPLACE(
                                                                                        REPLACE(
                                                                                            REPLACE(
                                                                                                Histologic_Type, ',', ''
                                                                                            ), 'tubular adenocarcinoma', '|TA|'
                                                                                        ), 'Tubular adenocarcinoma', '|TA|'
                                                                                    ), 'mucinous adenocarcinoma', '|MuA|'
                                                                                ), 'poorly cohesive carcinoma', '|PCC|'
                                                                            ), 'SRC', '|SRC|'
                                                                        ), 'non-|SRC|', '|non-SRC|'
                                                                    ), 'signet ring cell carcinoma', '|SRC|'
                                                                ), 'signet ring cell', '|SRC|'
                                                            ), 'mucinous carcinoma', '|MuC|'
                                                        ), 'medullary carcinoma', '|MDCA|'
                                                    ), 'Medullary carcinoma ', '|MDCA|'
                                                ), 'papillary adenocarcinoma', '|PA|'
                                            ), 'neuroendocrine carcinoma', '|NET|'
                                        ), 'neuroendocrine tumor', '|NET|'
                                    ), 'lymphoid stroma', '|LyS|'
                                ), 'PD', '|PD|'
                            ), 'tubular', '|TA|'
                        ), 'papillary', '|PA|'
                    ), 'mucinous', '|MuA|'
                ), 'component', ''
            ), 'mixed', ''
        ) AS Histologic_Type
    FROM (
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            CASE
                WHEN NULLIF(Histologic_Type_2, '') IS NOT NULL
                THEN REGEXP_REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                TRIM(
                                    TRAILING SUBSTR(Histologic_Type_2, INSTR(Histologic_Type_2, 'Tumor Site'))
                                    FROM Histologic_Type_2
                                ), 'WHO clASsification', ''
                            ), '(Histologic Type)', ''
                        ), '\n', ''
                    ), '[(|;|:|-|)]', ''
                )
                WHEN NULLIF(Histologic_Type, '') IS NOT NULL
                THEN REGEXP_REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        TRIM(
                                            TRAILING SUBSTR(Histologic_Type, INSTR(Histologic_Type, '\n'))
                                            FROM Histologic_Type
                                        ), 'histologic type:', ''
                                    ), 'poorly differentiated', ''
                                ), 'micropapillary carcinoma', ''
                            ), 'Histologic type', ''
                        ), '(WHO clASsification)', ''
                    ), '[(|.|;|:|)]', ''
                )
                ELSE SUBSTRING_INDEX(병리진단, '1)', 1)
            END AS Histologic_Type
        FROM (
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                병리진단,
                SUBSTR(병리진단, INSTR(병리진단, 'histologic type')) AS Histologic_Type,
                SUBSTR(
                    병리진단, INSTR(병리진단, 'WHO clASsification (Histologic Type)')
                ) AS Histologic_Type_2
            FROM pathologic_biopsy_03
        ) biopsy
    ) biopsy
)

SELECT
    원무접수ID,
    환자번호,
    검사시행일,
    COALESCE(
        Histologic_Type_1, Histologic_Type_5
    ) AS Histologic_Type
FROM (
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        Histologic_Type,
        NULLIF(
            REPLACE(
                REPLACE(
                    REPLACE(
                        CONCAT(
                            Histologic_Type_1, ',', Persent1, ',', Histologic_Type_2, ',', Persent2, ',', Histologic_Type_3, ',', Persent3, ',', Histologic_Type_4
                        ), 'NULL,', ''
                    ), ',NULL', ''
                ), 'NULL', ''
            ), ''
        ) AS Histologic_Type_1,
        Histologic_Type_5
    FROM (
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            Histologic_Type_1 AS Histologic_Type,
            CASE
                WHEN (CHAR_LENGTH(Histologic_Type_1) - CHAR_LENGTH(REPLACE(Histologic_Type_1, '|', ''))) >= 2
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(Histologic_Type_1, '|', 2), '|', -1)
                ELSE 'NULL'
            END AS Histologic_Type_1,
            CASE
                WHEN (CHAR_LENGTH(Histologic_Type_1) - CHAR_LENGTH(REPLACE(Histologic_Type_1, '|', ''))) >= 4
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(Histologic_Type_1, '|', 4), '|', -1)
                ELSE 'NULL'
            END AS Histologic_Type_2,
            CASE
                WHEN (CHAR_LENGTH(Histologic_Type_1) - CHAR_LENGTH(REPLACE(Histologic_Type_1, '|', ''))) >= 6
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(Histologic_Type_1, '|', 6), '|', -1)
                ELSE 'NULL'
            END AS Histologic_Type_3,
            CASE
                WHEN (CHAR_LENGTH(Histologic_Type_1) - CHAR_LENGTH(REPLACE(Histologic_Type_1, '|', ''))) = 8
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(Histologic_Type_1, '|', 8), '|', -1)
                ELSE 'NULL'
            END AS Histologic_Type_4,
            IFNULL(REGEXP_SUBSTR(Histologic_Type_1, '[0-9]+[0-9]?[%%]'), 'NULL') AS Persent1,
            IFNULL(REGEXP_SUBSTR(Histologic_Type_1, '[0-9]+[0-9]?[%%]', 1, 2), 'NULL') AS persent2,
            IFNULL(REGEXP_SUBSTR(Histologic_Type_1, '[0-9]+[0-9]?[%%]', 1, 3), 'NULL') AS Persent3,
            NULLIF(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            CONCAT(TA, ',', carcinoma), '0,', ''
                        ), ',0', ''
                    ), '0', ''
                ), ''
            ) AS Histologic_Type_5
        FROM (
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                CASE
                    WHEN (VER = 'VER1' OR VER = 'VER2')
                    THEN REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                REPLACE(
                                                    REPLACE(
                                                        REPLACE(
                                                            REPLACE(
                                                                REPLACE(
                                                                    REPLACE(
                                                                        REPLACE(
                                                                            REPLACE(
                                                                                REPLACE(
                                                                                    REPLACE(
                                                                                        REPLACE(
                                                                                            REPLACE(
                                                                                                REPLACE(
                                                                                                    REPLACE(
                                                                                                        REPLACE(
                                                                                                            REPLACE(
                                                                                                                Histologic_Type, ',', ''
                                                                                                            ), 'tubular adenocarcinoma', '|TA|'
                                                                                                        ), 'Tubular adenocarcinoma', '|TA|'
                                                                                                    ), 'mucinous adenocarcinoma', '|MuA|'
                                                                                                ), 'poorly cohesive carcinoma', '|PCC|'
                                                                                            ), 'SRC', '|SRC|'
                                                                                        ), 'non-|SRC|', '|non-SRC|'
                                                                                    ), 'signet ring cell carcinoma', '|SRC|'
                                                                                ), 'signet ring cell', '|SRC|'
                                                                            ), 'mucinous carcinoma', '|MuC|'
                                                                        ), 'medullary carcinoma', '|MDCA|'
                                                                    ), 'Medullary carcinoma ', '|MDCA|'
                                                                ), 'papillary adenocarcinoma', '|PA|'
                                                            ), 'neuroendocrine carcinoma', '|NET|'
                                                        ), 'neuroendocrine tumor', '|NET|'
                                                    ), 'lymphoid stroma', '|LyS|'
                                                ), 'PD', '|PD|'
                                            ), 'tubular', '|TA|'
                                        ), 'papillary', '|PA|'
                                    ), 'mucinous', '|MuA|'
                                ), 'component', ''
                            ), 'mixed', ''
                        ), 'non |SRC|', '|non SRC|'
                    )
                END Histologic_Type_1,
                CASE
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'tubular adenocarcinoma') THEN 'TA'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'mucinous adenocarcinoma') THEN 'MuA'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'papillary adenocarcinoma') THEN 'PA'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'adenocarcinoma') THEN 'TA'
                    ELSE 0
                END AS TA,
                CASE
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'poorly cohesive carcinoma') THEN 'PCC'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'signet ring cell carcinoma') THEN 'SRC'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'mucinous carcinoma') THEN 'MuC'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'medullary carcinoma') THEN 'MDCA'
                    WHEN VER = 'VER3' AND INSTR(Histologic_Type, 'neuroendocrine carcinoma') THEN 'NET'
                    ELSE 0
                END AS carcinoma
            FROM (
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    CASE
                        WHEN VER = 'VER1'
                        THEN REGEXP_REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        TRIM(
                                            TRAILING SUBSTR(Histologic_Type, INSTR(Histologic_Type, 'Tumor Site'))
                                            FROM Histologic_Type
                                        ), 'WHO classification', ''
                                    ), '(Histologic Type)', ''
                                ), '\n', ''
                            ), '[(|;|:|-|)]', ''
                        )
                        WHEN VER = 'VER2'
                        THEN REGEXP_REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                TRIM(
                                                    TRAILING SUBSTR(Histologic_Type, INSTR(Histologic_Type, '5'))
                                                    FROM Histologic_Type
                                                ), 'histologic type:', ''
                                            ), 'poorly differentiated', ''
                                        ), 'micropapillary carcinoma', ''
                                    ), 'Histologic type', ''
                                ), '(WHO classification)', ''
                            ), '[(|.|;|:|)]', ''
                        )
                        WHEN VER = 'VER3'
                        THEN Histologic_Type
                    END AS Histologic_Type,
                    VER
                FROM (
                    SELECT
                        원무접수ID,
                        환자번호,
                        검사시행일,
                        병리진단,
                        CASE
                            WHEN INSTR(병리진단, 'WHO classification (Histologic Type)') != 0
                            THEN SUBSTR(병리진단, INSTR(병리진단, 'WHO classification (Histologic Type)'))
                            WHEN INSTR(병리진단, 'histologic type') != 0
                            THEN SUBSTR(병리진단, INSTR(병리진단, 'histologic type'))
                            ELSE SUBSTRING_INDEX(병리진단, '\n', 6)
                        END AS Histologic_Type,
                        CASE
                            WHEN INSTR(병리진단, 'WHO classification (Histologic Type)') != 0
                            THEN 'VER1'
                            WHEN INSTR(병리진단, 'histologic type') != 0
                            THEN 'VER2'
                            ELSE 'VER3'
                        END AS VER
                    FROM pathologic_biopsy_03
                ) biopsy
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
