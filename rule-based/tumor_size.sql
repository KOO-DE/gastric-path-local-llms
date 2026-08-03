SELECT
    DISTINCT 원무접수ID,
    환자번호,
    검사시행일,
    CASE
        WHEN (Tumor_Size_Maj IS NOT NULL AND Tumor_Size_Min IS NOT NULL)
        THEN CONCAT(
            CONCAT(
                Tumor_Size_Maj, ' x '
            ), Tumor_Size_Min
        )
    END AS Tumor_Size,
    Size_Cmt,
    CASE
        WHEN (Tumor_Size_Maj IS NULL OR Tumor_Size_Min IS NULL)
        THEN 병리진단
    END AS Undecided
FROM(
    SELECT
    원무접수ID,
    환자번호,
    검사시행일,
    병리진단,
    CASE
        WHEN INSTR(Size_Cmt, 'mm') != 0
        THEN Tumor_Size_Maj * 0.1
        ELSE Tumor_Size_Maj
    END AS Tumor_Size_Maj,
    CASE
        WHEN INSTR(Size_Cmt, 'mm') != 0
        THEN Tumor_Size_Min * 0.1
        ELSE Tumor_Size_Min
    END AS Tumor_Size_Min,
    REPLACE(
        SUBSTR(
            Size_Cmt, INSTR(Size_Cmt, 'mm') + 2
        ), '.', ''
    ) AS Size_Cmt
FROM(
    SELECT
        원무접수ID,
        환자번호,
        검사시행일,
        병리진단,
        `Size`,
        REPLACE(
            REPLACE(
                REGEXP_REPLACE(
                    BINARY Size, '[0-9]+[.]?[0-9]?[0-9]?[ ]?[x][ ]?[0-9]+[.]?[0-9]?[0-9]?[ ]?', ''
                ), 'Size', ''
            ), 'cm', ''
        ) AS Size_Cmt,
        CASE
            WHEN NULLIF(Size, '') IS NULL
            THEN NULL
            WHEN REGEXP_INSTR(BINARY `Size`, '[0-9]+[.]?[0-9]?[0-9]?[ ]?[x][ ]?[0-9]+[.]?[0-9]?[0-9]?') != 0 
            THEN CONVERT(
                SUBSTRING_INDEX(
                    REGEXP_SUBSTR(
                        BINARY `Size`, '[0-9]+[.]?[0-9]?[0-9]?[ ]?[x][ ]?[0-9]+[.]?[0-9]?[0-9]?'
                    ), 'x', 1
                ), DECIMAL(5, 2)
            )
            WHEN INSTR(BINARY `Size`, 'x') != 0
            THEN CONVERT(
                REPLACE (
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            SUBSTRING_INDEX(
                                BINARY `Size`, 'x', 1
                            ), '[a-z]', ''
                        ), '[가-힣]', ''
                    ), ')', ''
                ), DECIMAL(5, 2)
            )
            END AS Tumor_Size_Maj,
            CASE
                WHEN NULLIF(`Size`, '') IS NULL
                THEN NULL
                WHEN REGEXP_INSTR(`Size`, '[0-9]+[.]?[0-9]?[0-9]?[ ]?[x][ ]?[0-9]+[.]?[0-9]?[0-9]?') != 0
                THEN CONVERT(
                    SUBSTRING_INDEX(
                        REGEXP_SUBSTR(
                            BINARY `Size`, '[0-9]+[.]?[0-9]?[0-9]?[ ]?[x][ ]?[0-9]+[.]?[0-9]?[0-9]?'
                        ), 'x', -1
                    ), DECIMAL(5, 2)
                )
                WHEN INSTR(`Size`, 'x') != 0
                THEN CONVERT(
                    REPLACE (
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                SUBSTRING_INDEX(
                                    SUBSTRING_INDEX(
                                        BINARY `Size`, 'x', 2
                                    ), 'x', -1
                                ), '[a-z]', ''
                            ), '[가-힣]', ''
                        ), ')', ''
                    ), DECIMAL(5, 2)
                )
            END AS Tumor_Size_Min
        FROM(
            SELECT
                원무접수ID,
                환자번호,
                검사시행일,
                병리진단,
                REGEXP_REPLACE(
                    REPLACE(
                        TRIM(
                            TRAILING SUBSTR(`Size`, INSTR(`Size`, '\n'))
                            FROM `Size`
                            ), 'size', ''
                        ), '[(|;|:|-|)]', ''
                ) AS `Size`
            FROM(
                SELECT
                    원무접수ID,
                    환자번호,
                    검사시행일,
                    병리진단,
                    SUBSTR(병리진단, INSTR(병리진단, 'size')) AS `Size`
                FROM pathologic_biopsy_03
            ) biopsy
        ) biopsy
    ) biopsy
) biopsy
