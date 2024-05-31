DROP TABLE IF EXISTS urls;
DROP TABLE IF EXISTS url_checks;


CREATE TABLE urls (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP
);
CREATE TABLE url_checks (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id INT REFERENCES urls (id),
    status_code INT,
    h1 VARCHAR(255),
    title VARCHAR(255),
    description VARCHAR(255),
    created_at TIMESTAMP
);