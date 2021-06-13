ALTER TABLE fabrikApi.content ADD agg_rating_avg FLOAT;
ALTER TABLE fabrikApi.content ADD agg_rating_count INT;
ALTER TABLE fabrikApi.stage_progression ADD date_last_day_session datetime;
ALTER TABLE fabrikApi.stage_progression ADD date_completed datetime;
