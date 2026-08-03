WITH step1 AS (
    SELECT
        DISTINCT 원무접수ID,
        환자번호,
        검사시행일,
        pTNM_ver,
        CASE
            WHEN NULLIF(pT_1, '') IS NULL
            THEN (CASE
                    WHEN (pT_2 = '(pTNM)') = 1
                    THEN CONCAT(
                        CONCAT(pT_4, REPLACE(pT_5, 'p', '')),
                        TRIM(REPLACE(pT_6, 'Not applicable', 'Mx'))
                    )
                    WHEN (NULLIF(pT_2, '') IS NOT NULL AND NULLIF(pT_3, '') IS NOT NULL)
                    THEN CONCAT(
                        CONCAT(
                            SUBSTRING_INDEX(SUBSTRING_INDEX(pT_2, ')', 1), '(', -1),
                            REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(pT_3, ')', 1), '(', -1), 'p', '')
                        ), 'Mx'
                    )
                    WHEN NULLIF(pT_2, '') IS NOT NULL
                    THEN CONCAT(
                        CONCAT(SUBSTRING_INDEX(SUBSTRING_INDEX(pT_2, ')', 1), '(', -1), 'Nx'),
                        'Mx'
                    )
                    WHEN NULLIF(pT_3, '') IS NOT NULL
                    THEN CONCAT(
                        CONCAT('pTx', REPLACE(SUBSTRING_INDEX(SUBSTRING_INDEX(pT_3, ')', 1), '(', -1), 'p', '')),
                        'Mx'
                    )
                    ELSE NULL
                END
            )
            WHEN INSTR(pT_1, 'M') = 0
            THEN CONCAT(pT_1, 'Mx')
            ELSE pT_1
        END AS pT,
        CASE
            WHEN INSTR(SUBSTR(pT_1, INSTR(pT_1, 'Comment'), INSTR(pT_1, ')') - INSTR(pT_1, 'Comment')), '2') != 0
            THEN SUBSTRING_INDEX(`Comment`, '\n', 5)
            WHEN INSTR(SUBSTR(pT_1, INSTR(pT_1, 'Comment'), INSTR(pT_1, ')') - INSTR(pT_1, 'Comment')), 'Comment') != 0
            THEN SUBSTRING_INDEX(`Comment`, '\n', 3)
        END AS `Comment`
    FROM (
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            REPLACE(
                REPLACE(
                    REPLACE(
                        TRIM(TRAILING SUBSTR(pT_1, INSTR(pT_1, '\n')) FROM pT_1),
                        'pTNM stage (by AJCC 8th edition):', ''
                    ), 'pTNM stage', ''
                ), ':', ''
            ) AS pT_1,
            CASE
                WHEN (NULLIF(pT_7, '') IS NOT NULL AND NULLIF(pT_4, '') IS NULL)
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(pT_7, 'Lymph Nodes', 1), 'Primary Tumor', -1)
                ELSE TRIM(TRAILING SUBSTR(pT_2, INSTR(pT_2, '\n')) FROM pT_2)
            END AS pT_2,
            CASE
                WHEN (NULLIF(pT_7, '') IS NOT NULL AND NULLIF(pT_4, '') IS NULL)
                THEN SUBSTRING_INDEX(SUBSTRING_INDEX(pT_7, 'Distant Metastasis', 1), 'Lymph Nodes', -1)
                ELSE TRIM(TRAILING SUBSTR(pT_3, INSTR(pT_3, '\n')) FROM pT_3)
            END AS pT_3,
            REGEXP_REPLACE(
                SUBSTR(
                    SUBSTRING_INDEX(SUBSTRING_INDEX(pT_4, 'Tumor invades', 1), 'Primary Tumor (pT)', -1),
                    INSTR(SUBSTRING_INDEX(SUBSTRING_INDEX(pT_4, 'Tumor invades', 1), 'Primary Tumor (pT)', -1), 'pT'), 4
                ), '[:|,]', ''
            ) AS pT_4,
            REPLACE(
                SUBSTR(
                    SUBSTRING_INDEX(SUBSTRING_INDEX(pT_5, 'Greater curvature', 1), 'Lymph Nodes (pN)', -1),
                    INSTR(SUBSTRING_INDEX(SUBSTRING_INDEX(pT_5, 'Greater curvature', 1), 'Lymph Nodes (pN)', -1), 'pN'), 4
                ), ':', ''
            ) AS pT_5,
            REPLACE(
                SUBSTRING_INDEX(SUBSTRING_INDEX(pT_6, '5) Resection margins', 1), 'Distant Metastasis (pM)', -1),
                '\n', ''
            ) AS pT_6,
            CASE
                WHEN INSTR(pT_1, 'Comment') != 0
                THEN SUBSTR(`Comment`, INSTR(`Comment`, '* Comment'))
                ELSE NULL
            END AS `Comment`,
            SUBSTR(
                TRIM(TRAILING SUBSTR(pT_1, INSTR(pT_1, '\n')) FROM pT_1),
                INSTR(pT_1, 'by'), 19
            ) AS pTNM_ver
        FROM (
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                SUBSTR(병리진단, INSTR(병리진단, 'pTNM stage')) AS pT_1,
                SUBSTR(병리진단, INSTR(병리진단, '(pT')) AS pT_2,
                SUBSTR(병리진단, INSTR(병리진단, '(pN')) AS pT_3,
                SUBSTR(병리진단, INSTR(병리진단, 'Primary Tumor (pT)')) AS pT_4,
                SUBSTR(병리진단, INSTR(병리진단, 'Lymph Nodes (pN)')) AS pT_5,
                SUBSTR(병리진단, INSTR(병리진단, 'Distant Metastasis (pM)')) AS pT_6,
                SUBSTR(병리진단, INSTR(병리진단, 'Pathologic Staging (pTNM)')) AS pT_7,
                SUBSTR(병리진단, INSTR(병리진단, 'Comment')) AS `Comment`
            FROM pathology_report
        ) biopsy
    ) biopsy
)

SELECT
    환자번호,
    원무접수ID,
    검사시행일,
    pTNM_ver,
    pT,
    pN,
    pM,
    CASE
        WHEN ((pT = 'T1' OR pT = 'T1a' OR pT = 'T1b') AND pN = 'N0' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IA'
        WHEN pT = 'T2' AND pN = 'N0' AND (pM = 'M0' OR pM = 'Mx')
        THEN 'IB'
        WHEN ((pT = 'T1' OR pT = 'T1a' OR pT = 'T1b') AND pN = 'N1' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IB'
        WHEN (pT = 'T3' AND pN = 'N0' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIA'
        WHEN (pT = 'T2' AND pN = 'N1' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIA'
        WHEN ((pT = 'T1' OR pT = 'T1a' OR pT = 'T1b') AND pN = 'N2' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIA'
        WHEN (pT = 'T4a' AND pN = 'N0' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIB'
        WHEN (pT = 'T3' AND pN = 'N1' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIB'
        WHEN (pT = 'T2' AND pN = 'N2' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIB'
        WHEN ((pT = 'T1' OR pT = 'T1a' OR pT = 'T1b') AND pN = 'N3a' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIB'
        WHEN ((pT = 'T1' OR pT = 'T1a' OR pT = 'T1b') AND pN = 'N3b' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIB'
        WHEN (pT = 'T4a' AND pN = 'N1' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIA'
        WHEN (pT = 'T3' AND pN = 'N2' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIA'
        WHEN (pT = 'T2' AND pN = 'N3a' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIA'
        WHEN (pT = 'T2' AND pN = 'N3b' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIA'
        WHEN (pT = 'T4b' AND (pN = 'NO' OR pN = 'N0' OR pN = 'N1') AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIB'
        WHEN (pT = 'T4a' AND pN = 'N2' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIB'
        WHEN (pT = 'T3' AND pN = 'N3a' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIB'
        WHEN (pT = 'T3' AND pN = 'N3b' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIB'
        WHEN (pT = 'T4b' AND (pN = 'N2' OR pN = 'N3a') AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIC'
        WHEN (pT = 'T4b' AND (pN = 'N2' OR pN = 'N3b') AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIC'
        WHEN (pT = 'T4a' AND pN = 'N3a' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIC'
        WHEN (pT = 'T4a' AND pN = 'N3b' AND (pM = 'M0' OR pM = 'Mx'))
        THEN 'IIIC'
        WHEN ((pT != 'Tx' OR pT != 'None' OR pT != NULL) AND (pN != 'Nx' OR pN != 'None' OR pN != NULL) AND pM = 'M1')
        THEN 'IV'
    END AS Staging,
    pTNM_Comment
FROM (
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        CASE
            WHEN INSTR(pT, 'x') != 0 THEN 'Tx'
            WHEN INSTR(pT, '1a') != 0 THEN 'T1a'
            WHEN INSTR(pT, '1b') != 0 THEN 'T1b'
            WHEN INSTR(pT, '2') != 0 THEN 'T2'
            WHEN INSTR(pT, '3') != 0 THEN 'T3'
            WHEN INSTR(pT, '4a') != 0 THEN 'T4a'
            WHEN INSTR(pT, '4b') != 0 THEN 'T4b'
            WHEN NULLIF(pT, '') IS NULL THEN NULL
        END AS pT,
        CASE
            WHEN INSTR(pN, 'x') != 0 THEN 'Nx'
            WHEN INSTR(pN, '0') != 0 THEN 'N0'
            WHEN INSTR(pN, '1') != 0 THEN 'N1'
            WHEN INSTR(pN, '2') != 0 THEN 'N2'
            WHEN INSTR(pN, '3a') != 0 THEN 'N3a'
            WHEN INSTR(pN, '3b') != 0 THEN 'N3b'
            WHEN NULLIF(pN, '') IS NULL THEN 'None'
        END AS pN,
        CASE
            WHEN INSTR(pM, 'x') != 0 THEN 'Mx'
            WHEN INSTR(pM, '0') != 0 THEN 'M0'
            WHEN INSTR(pM, '1') != 0 THEN 'M1'
            WHEN NULLIF(pM, '') IS NULL THEN 'None'
        END AS pM,
        pTNM_Comment,
        pTNM_ver
    FROM (
        SELECT
            원무접수ID,
            환자번호,
            검사시행일,
            pTNM_ver,
            REPLACE(
                REPLACE(
                    SUBSTR(pT, INSTR(pT, 'pT') + 2, (INSTR(pT, 'N') - 1) - (INSTR(pT, 'pT') + 1)),
                    ',', ''
                ), 'p', ''
            ) AS pT,
            REPLACE(
                SUBSTR(pT, INSTR(pT, 'N') + 1, (INSTR(pT, 'M') - 1) - (INSTR(pT, 'N'))),
                ',', ''
            ) AS pN,
            REPLACE(SUBSTR(pT, INSTR(pT, 'M') + 1, 1), ',', '') AS pM,
            `Comment` AS pTNM_Comment
        FROM step1
    ) biopsy
) biopsy
