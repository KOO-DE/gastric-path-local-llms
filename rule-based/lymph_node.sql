SELECT
    원무접수ID,
    환자번호,
    검사시행일,
    Lymph_Node,
    (Slash_01 + Slash_02 + Slash_03 + Slash_04 + Slash_05 + Slash_06 + Slash_07 + Slash_08 + Slash_09 + Slash_10 + Slash_11 + Slash_12 + Slash_13) AS metLN,
    (Slash2_01 + Slash2_02 + Slash2_03 + Slash2_04 + Slash2_05 + Slash2_06 + Slash2_07 + Slash2_08 + Slash2_09 + Slash2_10 + Slash2_11 + Slash2_12 + Slash2_13) AS harvLN
FROM(
    SELECT *, 
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 1), '/', ''
                ), '0'
            ) AS Slash_01,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 2
                ), '/', ''
            ), '0'
        ) AS Slash_02,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 3
                ), '/', ''
            ), '0'
        ) AS Slash_03,
        IFNULL(
            REPLACE (
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 4
                ), '/', ''
            ), '0'
        ) AS Slash_04,
        IFNULL(
            REPLACE (
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 5
                ), '/', ''
            ), '0'
        ) AS Slash_05,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 6
                ), '/', ''
            ), '0'
        ) AS Slash_06,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 7
                ), '/', ''
            ), '0'
        ) AS Slash_07,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 8
                ), '/', ''
            ), '0'
        ) AS Slash_08,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 9
                ), '/', ''
            ), '0'
        ) AS Slash_09,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 10
                ), '/', ''
            ), '0'
        ) AS Slash_10,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 11
                ), '/', ''
            ), '0'
        ) AS Slash_11,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 12
                ), '/', ''
            ), '0'
        ) AS Slash_12,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[0-9]+[/]', 1, 13
                ), '/', ''
            ), '0'
        ) AS Slash_13,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 1
                ), '/', ''
            ), '0'
        ) AS Slash2_01,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 2
                ), '/', ''
            ), '0'
        ) AS Slash2_02,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 3
                ), '/', ''
            ), '0'
        ) AS Slash2_03,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 4
                ), '/', ''
            ), '0'
        ) AS Slash2_04,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 5
                ), '/', ''
            ), '0'
        ) AS Slash2_05,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 6
                ), '/', ''
            ), '0'
        ) AS Slash2_06,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 7
                ), '/', ''
            ), '0'
        ) AS Slash2_07,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 8
                ), '/', ''
            ), '0'
        ) AS Slash2_08,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 9
                ), '/', ''
            ), '0'
        ) AS Slash2_09,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 10
                ), '/', ''
            ), '0'
        ) AS Slash2_10,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 11
                ), '/', ''
            ), '0'
        ) AS Slash2_11,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 12
                ), '/', ''
            ), '0'
        ) AS Slash2_12,
        IFNULL(
            REPLACE(
                REGEXP_SUBSTR(
                    Lymph_Node, '[/][0-9]+', 1, 13
                ), '/', ''
            ), '0'
        ) AS Slash2_13
    FROM(
        SELECT *,
            SUBSTRING_INDEX(
                SUBSTR(
                    병리진단, REGEXP_INSTR(병리진단, '[(][0-9]+[/][0-9]+.')
                ), ')', 1
            ) AS Lymph_Node
        FROM pathologic_biopsy_03
    ) a
) a
