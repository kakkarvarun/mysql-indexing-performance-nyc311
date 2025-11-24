-- drop existing indexes (ignore errors by running twice only if needed)
DROP INDEX idx_borough_created ON nyc311;
DROP INDEX idx_created ON nyc311;
DROP INDEX ft_desc ON nyc311;
