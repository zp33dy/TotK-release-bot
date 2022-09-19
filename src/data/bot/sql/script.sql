CREATE TABLE IF NOT EXISTS guilds (
    channel_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL PRIMARY KEY,
    message_id BIGINT
);
