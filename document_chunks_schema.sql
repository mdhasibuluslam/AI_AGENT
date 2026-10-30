
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    file_id BIGINT NOT NULL
        REFERENCES uploaded_files(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),

    chunk_text TEXT NOT NULL
        CHECK (length(chunk_text) > 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (file_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_user_file
    ON document_chunks (user_id, file_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_file_order
    ON document_chunks (file_id, chunk_index);
