# R_bagimsiz_tekrar.R — Independent replication in R of the age-standardised rates and principal rank statistics.
# Run from the repository root (setwd to the repository folder). Packages: data.table, jsonlite, MASS.
# Output: results/tables/R_tekrar_karsilastirma.csv (Python value, R value, difference). Comments in the body are in Turkish.
suppressPackageStartupMessages({ library(data.table); library(jsonlite); library(MASS) })

w   <- fread("data/weights/agirliklar_100bin_ANALIZ.csv")
std <- c("segi_doll", "who2001", "gbd2021", "who2026")
stopifnot(all(abs(colSums(w[, ..std]) - 1e5) < 0.01))

d <- fread(cmd = if (.Platform$OS.type == "windows") NULL else "gzip -dc data/raw/globocan_yasaozgu_2022_2024.csv.gz")
n_ham <- nrow(d); d <- unique(d)                                         # kanser 39 satırları ham dosyada iki kez çekilmiş (birebir aynı kopyalar)
cat("Ham satır:", n_ham, "· tekil satır:", nrow(d), "\n")
stopifnot(!anyDuplicated(d, by = c("yil","olcut","cinsiyet","ulke_kodu","kanser_kodu","age_code")))
d[, ulke_kodu := fifelse(ulke_kodu == 160L, 156L, ulke_kodu)]          # Çin kodu
key <- c("yil", "olcut", "cinsiyet", "ulke_kodu", "kanser_kodu")
wide <- dcast(d, as.formula(paste(paste(key, collapse = "+"), "~ age_code")), value.var = c("vaka", "nufus"))

der <- function(v, a) {                                                # 18 yaş grubu
  x <- sapply(0:14, function(i) v[[paste0(a, "_", i)]])
  cbind(x, v[[paste0(a, "_115")]] - v[[paste0(a, "_14")]],
           v[[paste0(a, "_116")]] - v[[paste0(a, "_115")]],
           v[[paste0(a, "_117")]] - v[[paste0(a, "_116")]])
}
C <- der(wide, "vaka"); P <- der(wide, "nufus")
stopifnot(all(rowSums(C) == wide$vaka_99), all(rowSums(P) == wide$nufus_99))
R <- ifelse(P > 0, C / P * 1e5, 0)
for (s in std) wide[[paste0("asr_", s)]] <- as.vector(R %*% w[[s]] / 1e5)

# Pozitif kontrol: Segi ASR = IARC ASR
iarc <- d[age_code == 99, .(asr_iarc = asr_iarc[1]), by = key]
wide <- merge(wide, iarc, by = key)
cat("Segi − IARC en büyük |fark|:", max(abs(round(wide$asr_segi_doll, 2) - wide$asr_iarc)), "\n")

# Ana karşılaştırma: Spearman ρ, ilk-10, ≥20 sıra kayması (Segi ↔ WHO 2026)
MAIN <- data.table(kanser_kodu = c(39,15,20,41,27,7,32,11,30,23,34,13,6,36), cinsiyet = c(0,0,2,0,1,0,0,0,0,2,0,0,0,0))
common <- intersect(wide[yil == 2022, unique(ulke_kodu)], wide[yil == 2024, unique(ulke_kodu)])
res <- rbindlist(lapply(c(2024, 2022), function(y) rbindlist(lapply(0:1, function(m) rbindlist(lapply(seq_len(nrow(MAIN)), function(i) {
  x <- wide[yil == y & olcut == m & cinsiyet == MAIN$cinsiyet[i] & kanser_kodu == MAIN$kanser_kodu[i] & vaka_99 > 0]
  if (y == 2022) x <- x[ulke_kodu %in% common]
  ra <- rank(-x$asr_segi_doll); rb <- rank(-x$asr_who2026)
  data.table(yil = y, olcut = m, kanser_kodu = MAIN$kanser_kodu[i], n = nrow(x),
             rho_R = cor(x$asr_segi_doll, x$asr_who2026, method = "spearman"),
             top10_R = length(intersect(x$ulke_kodu[order(-x$asr_segi_doll)][1:10], x$ulke_kodu[order(-x$asr_who2026)][1:10])) / 10,
             kayma20_R = sum(abs(ra - rb) >= 20))
}))))))

py <- fread("results/tables/T2_sira_uyumu.csv")[std_a == "segi_doll" & std_b == "who2026"]
meta <- fromJSON("data/raw/globocan_meta_2022_2024.json")
lab <- setNames(meta$meta2024$c$label, meta$meta2024$c$cancer)
res[, kanser := lab[as.character(kanser_kodu)]][, olcut_ad := fifelse(olcut == 0, "insidans", "mortalite")]
cmp <- merge(res, py[, .(yil, olcut_ad = olcut, kanser, rho_Py = rho, top10_Py = top10, kayma20_Py = kayma20)], by = c("yil", "olcut_ad", "kanser"))
cmp[, `:=`(rho_fark = round(rho_R - rho_Py, 4), top10_fark = top10_R - top10_Py, kayma20_fark = kayma20_R - kayma20_Py)]
fwrite(cmp, "results/tables/R_tekrar_karsilastirma.csv")
cat("Karşılaştırılan tabaka:", nrow(cmp), "\n")
cat("ρ en büyük |fark|:", max(abs(cmp$rho_fark)), " · ilk-10 farklı:", sum(cmp$top10_fark != 0), " · ≥20 kayma farklı:", sum(cmp$kayma20_fark != 0), "\n")
cat(if (max(abs(cmp$rho_fark)) < 1e-3 && all(cmp$top10_fark == 0)) "SONUÇ: Python ve R UYUMLU\n" else "SONUÇ: FARK VAR — inceleyin\n")
