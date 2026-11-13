| Dataset | Column | Data Type | Role (suy luận) | Unique Values | Missing Count | Missing Percentage |
|---|---|---|---|---|---|---|
| box_office_detailed | theater_count | float64 | rỗng 100% | 0 | 29,527 | 100.00 |
| box_office_detailed | opening_weekend_gross | float64 | số | 2,368 | 27,143 | 91.93 |
| box_office_detailed | domestic_gross | float64 | số | 2,610 | 26,902 | 91.11 |
| movies_raw | production_budget | float64 | số | 940 | 35,679 | 89.49 |
| box_office_raw | global_gross | float64 | số | 4,066 | 35,381 | 88.74 |
| rt_scores | critic_score | float64 | số | 101 | 33,488 | 83.99 |
| box_office_detailed | international_gross | float64 | số | 5,956 | 23,539 | 79.72 |
| rt_scores | audience_score | float64 | số | 100 | 28,520 | 71.53 |
| rt_scores | rt_url | str | text / categorical | 17,101 | 19,721 | 49.46 |
| movies_raw | imdb_id | str | định danh | 29,536 | 10,335 | 25.92 |
| movies_raw | production_company_ids | str | đa trị ('\|') | 14,348 | 8,353 | 20.95 |
| movies_raw | genre_ids | str | đa trị ('\|') | 3,833 | 7,035 | 17.64 |
| movies_raw | director_ids | str | đa trị ('\|') | 13,002 | 4,908 | 12.31 |
| movies_raw | lead_cast_ids_superset | str | đa trị ('\|') | 34,535 | 3,542 | 8.88 |
| credits_raw | billing_order | float64 | số | 451 | 41,116 | 6.43 |
| movies_raw | release_date_ref | str | ngày (text) | 16,580 | 754 | 1.89 |
| movies_raw | release_month | float64 | định danh/rời rạc | 12 | 754 | 1.89 |
| movies_raw | tmdb_collection_id | float64 | định danh/rời rạc | 9,728 | 30 | 0.08 |