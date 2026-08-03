SELECT
    DISTINCT
    원무접수ID,
    환자번호,
    검사시행일,
    CASE
        WHEN NULLIF(LVI_1, '') IS NULL
        THEN 'No'
        WHEN INSTR(LVI_1, 'absent') != 0
        THEN 'No'
        ELSE 'Yes'
    END AS LVI,
    LVI_2,
    CASE
        WHEN NULLIF(PNI_1, '') IS NULL
        THEN 'No'
        WHEN INSTR(PNI_1, 'absent') != 0
        THEN 'No'
        ELSE 'Yes'
    END AS PNI,
    PNI_2
FROM(
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        SUBSTR(LVI, 1, INSTR(LVI, ',') -1) AS LVI_1,
        REPLACE(SUBSTR(LVI, INSTR(LVI, ',') + 1), ',', '') AS LVI_2,
        REGEXP_REPLACE(PNI, '[^[:alnum:][:space:]]+', '') AS PNI_1,
        REGEXP_REPLACE(PNI, '[a-z]', '') AS PNI_2
    FROM(
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            REPLACE(
                REPLACE(
                    REPLACE(
                        Lymphovascular_Invasion, 'pending', 'pending,'
                    ), 'present', 'present,'
                ), 'absent', 'absent,'
            ) AS LVI,
            Perineural_Invasion AS PNI
        FROM(
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                REGEXP_REPLACE(
                    REPLACE(
                        REPLACE(
                            TRIM(
                                TRAILING SUBSTR(Lymphovascular_Invasion, INSTR(Lymphovascular_Invasion, '\n'))
                                FROM Lymphovascular_Invasion
                            ), 'lymphovascular invasion', ''
                        ), 'Lymphovascular invasion', ''
                    ), '[(|.|;|:|)]', ''
                ) AS Lymphovascular_Invasion,
                REGEXP_REPLACE(
                    REPLACE(
                        TRIM(
                            TRAILING SUBSTR(Perineural_Invasion, INSTR(Perineural_Invasion, '\n'))
                            FROM Perineural_Invasion
                        ), 'perineural invasion', ''
                    ), '[(|.|;|:|)]', ''
                ) AS Perineural_Invasion
            FROM(
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    SUBSTR(병리진단, INSTR(병리진단, 'lymphovascular invasion')) AS Lymphovascular_Invasion,
                    SUBSTR(병리진단, INSTR(병리진단, 'perineural invasion')) AS Perineural_Invasion
                FROM  pathology_report
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
