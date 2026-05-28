-- ============================================================
--  Sistema de Empréstimos TI — UniFecaf & ColégioSER
-- ============================================================

CREATE DATABASE IF NOT EXISTS emprestimos_ti
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE emprestimos_ti;

-- Tabela de Equipamentos
CREATE TABLE IF NOT EXISTS equipamentos (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nome        VARCHAR(100) NOT NULL,
  patrimonio  VARCHAR(50)  NOT NULL UNIQUE,
  descricao   VARCHAR(255),
  ativo       BOOLEAN DEFAULT TRUE,
  criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Empréstimos
CREATE TABLE IF NOT EXISTS emprestimos (
  id                           INT AUTO_INCREMENT PRIMARY KEY,
  equipamento_id               INT NOT NULL,
  responsavel                  VARCHAR(100) NOT NULL,
  email                        VARCHAR(150) NOT NULL,
  local_uso                    VARCHAR(100) NOT NULL,
  instituicao                  ENUM('UniFECAF','ColégioSER') NOT NULL,
  turno                        ENUM('manha','noite','outro') NOT NULL DEFAULT 'outro',
  data_hora_entrega            DATETIME NOT NULL,
  data_hora_devolucao_prevista DATETIME NOT NULL,
  data_hora_devolucao_real     DATETIME NULL,
  observacoes                  TEXT,
  status                       ENUM('ativo','devolvido','em_atraso') NOT NULL DEFAULT 'ativo',
  criado_em                    DATETIME DEFAULT CURRENT_TIMESTAMP,
  atualizado_em                DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
);