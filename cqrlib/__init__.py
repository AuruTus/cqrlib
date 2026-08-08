# make sure there is no mp func otherwise import individual func instead

from cqrlib.Util.multiprocess import mp_pandas_obj, opt_num_threads, process_jobs_, process_jobs
from cqrlib.Util.volatility import *
from cqrlib.Util.indicator import bband_as_side, bband_frac, bband_std, side_pick

from cqrlib.Util.bsm_model import *
from cqrlib.Util.opt_prob_calculator import *

from cqrlib.Sample_data.make_data import (
    make_classification_data,
    create_price_data,
    make_randomt1_data,
    create_portfolio,
    generate_HRP_data,
)

# from cqrlib.Tools.root_methods import *
from cqrlib.Tools.stats_rpt import normality, unit_root, report_matrix, white_random, feat_imp
from cqrlib.Tools.cross_validate import train_times, embargo_times, PurgedKFold, cv_score, hyper_fit
from cqrlib.Tools.metrics import mdi, mda, sfi, mp_sfi, sample_weight_generator, plot_feat_imp, feat_imp_analysis
from cqrlib.Tools.feat_PCA import o_feat, feat_pca

from cqrlib.Labels.triple_barrier_method import _pt_sl_t1, vert_barrier, tri_barrier, meta_label, drop_label
from cqrlib.Labels.percentile_score import rolling_percentileofscore

from cqrlib.Filters.filters import cs_filter

from cqrlib.Sampling.sample_unique import (
    wght_by_coevents,
    num_co_events,
    av_unique,
    idx_matrix,
    mp_idx_matrix,
    seq_bts,
    mp_seq_bts,
    MC_seq_bts,
    MT_MC,
    wght_by_rtn,
    wght_by_td,
)

from cqrlib.Features.fractional_diff import fracDiff_FFD, fracDiff, min_value, plot_min_ffd
# from cqrlib.Features.futures_roll import *
# from cqrlib.Features.PCA_weight_dist import *

from cqrlib.Ensemble.seq_bts_bagging import BaggingClassifier, BaggingRegressor

from cqrlib.Risk_mgmt.bet_size import avg_active_signals, discrete_signal, get_signal, dynamic_bet, co_bets_size
from cqrlib.Risk_mgmt.ef3m import mts_fit, m_bet_EF3M

from cqrlib.Back_test.opt_trade_rule import opt_tr
from cqrlib.Back_test.stats_measure import (
    ff_time,
    ave_hp,
    rtn_by_tw,
    hh_idx,
    drawdn_period,
    annualized_rtn,
    sharpe_ratio,
    inform_ratio,
    proba_sr,
    deflated_sr,
    min_tr_len,
)

from cqrlib.Portfolio_opt.risk_est import RiskEstimators
from cqrlib.Portfolio_opt.rtn_est import ReturnsEstimators
from cqrlib.Portfolio_opt.risk_metrics import RiskMetrics
from cqrlib.Portfolio_opt.hrp import HRP
from cqrlib.Portfolio_opt.cla import CLA
from cqrlib.Portfolio_opt.mv import MV
from cqrlib.Portfolio_opt.nco import NCO
