USE yantu408;
INSERT INTO user(email, username, nickname, password_hash)
VALUES ('demo@turing408.ai', 'demo', '林同学', 'please-run-backend-seed-script')
ON DUPLICATE KEY UPDATE nickname = VALUES(nickname);
