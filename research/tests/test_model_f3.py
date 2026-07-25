"""
tests/test_model_f3.py

Sprint 32 Phase 1 — contract tests for the F3 late-fusion architecture,
written BEFORE the implementation. These tests ARE the specification:

  * two separate encoders (GOES, Aditya-L1) with disjoint parameters
  * independent normalization per stream (no shared norm/embedding params)
  * fusion applied ONLY after both latent embeddings exist
  * no information crosses between streams before the fusion point
  * availability/staleness channels are propagated to the Aditya stream
    (identically to Sprint 31: they are input channels, indices 32..35)
  * deterministic under seed control
  * documented parameter budget vs the single-encoder Sprint 31 model
"""
import torch

from app.services.ml.model_f3 import LateFusionPatchTST, GOES_DIM, ADITYA_DIM, TOTAL_DIM
from app.services.ml.model import PatchTST


def _model():
    torch.manual_seed(0)
    return LateFusionPatchTST()


def test_dimensions_match_f2_layout():
    # F2 dataset is 36 channels: 17 GOES + 15 Aditya + 4 disclosure = 17 + 19
    assert GOES_DIM == 17
    assert ADITYA_DIM == 19
    assert TOTAL_DIM == 36


def test_forward_shape():
    m = _model().eval()
    x = torch.randn(8, 360, TOTAL_DIM)
    y = m(x)
    assert y.shape == (8, 1)


def test_two_separate_encoders_disjoint_params():
    m = _model()
    goes_ids = {id(p) for p in m.goes_encoder.parameters()}
    adit_ids = {id(p) for p in m.aditya_encoder.parameters()}
    assert goes_ids.isdisjoint(adit_ids)
    # each stream has its OWN patch embedding and norm (independent normalization)
    assert id(m.goes_encoder.patch_embed.projection.weight) != \
           id(m.aditya_encoder.patch_embed.projection.weight)
    assert id(m.goes_encoder.norm.weight) != id(m.aditya_encoder.norm.weight)


def test_goes_encoder_sees_only_goes_channels():
    m = _model().eval()
    x = torch.randn(4, 360, TOTAL_DIM)
    eg0, ea0 = m.forward_streams(x)
    # perturb ONLY Aditya channels (17..35): GOES embedding must be unchanged
    x2 = x.clone()
    x2[..., GOES_DIM:] += 5.0
    eg1, ea1 = m.forward_streams(x2)
    assert torch.allclose(eg0, eg1, atol=1e-6), "GOES stream leaked Aditya info before fusion"
    assert not torch.allclose(ea0, ea1), "Aditya encoder ignored its own inputs"


def test_aditya_encoder_sees_only_aditya_channels():
    m = _model().eval()
    x = torch.randn(4, 360, TOTAL_DIM)
    eg0, ea0 = m.forward_streams(x)
    # perturb ONLY GOES channels (0..16): Aditya embedding must be unchanged
    x2 = x.clone()
    x2[..., :GOES_DIM] += 5.0
    eg1, ea1 = m.forward_streams(x2)
    assert torch.allclose(ea0, ea1, atol=1e-6), "Aditya stream leaked GOES info before fusion"
    assert not torch.allclose(eg0, eg1), "GOES encoder ignored its own inputs"


def test_disclosure_channels_feed_aditya_stream():
    # channels 32..35 (availability/staleness) must reach the Aditya encoder,
    # not the GOES encoder — Sprint-31-identical mask propagation
    m = _model().eval()
    x = torch.randn(4, 360, TOTAL_DIM)
    eg0, ea0 = m.forward_streams(x)
    x2 = x.clone()
    x2[..., 32:36] += 3.0
    eg1, ea1 = m.forward_streams(x2)
    assert torch.allclose(eg0, eg1, atol=1e-6)
    assert not torch.allclose(ea0, ea1)


def test_fusion_depends_on_both_streams():
    m = _model().eval()
    x = torch.randn(4, 360, TOTAL_DIM)
    y0 = m(x)
    xg = x.clone(); xg[..., :GOES_DIM] += 2.0
    xa = x.clone(); xa[..., GOES_DIM:] += 2.0
    assert not torch.allclose(y0, m(xg)), "logit ignores GOES stream"
    assert not torch.allclose(y0, m(xa)), "logit ignores Aditya stream"


def test_fusion_is_after_pooling():
    # the fusion head consumes exactly the two pooled embeddings concatenated
    m = _model().eval()
    x = torch.randn(3, 360, TOTAL_DIM)
    eg, ea = m.forward_streams(x)
    assert eg.shape == (3, m.embed_dim)
    assert ea.shape == (3, m.embed_dim)
    fused = torch.cat([eg, ea], dim=-1)
    assert m.fusion_head.in_features == 2 * m.embed_dim
    y_direct = m.fusion_head(fused)
    assert torch.allclose(y_direct, m(x), atol=1e-6)


def test_determinism_under_seed():
    torch.manual_seed(123); m1 = LateFusionPatchTST()
    torch.manual_seed(123); m2 = LateFusionPatchTST()
    x = torch.randn(5, 360, TOTAL_DIM)
    m1.eval(); m2.eval()
    assert torch.allclose(m1(x), m2(x), atol=1e-7)


def test_parameter_budget_documented():
    m = _model()
    n = sum(p.numel() for p in m.parameters() if p.requires_grad)
    single = sum(p.numel() for p in PatchTST(n_features=36).parameters() if p.requires_grad)
    # two encoders: strictly more than the single-encoder model, under ~2.1x
    assert n > single
    assert n < 2.1 * single
    assert n < 10_000_000  # global cap


def test_no_sigmoid_raw_logit():
    m = _model().eval()
    x = torch.randn(64, 360, TOTAL_DIM) * 10
    y = m(x)
    # raw logits can exceed [0,1]; a sigmoid output could not
    assert (y.abs() > 1).any()
