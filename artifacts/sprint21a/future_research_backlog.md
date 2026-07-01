# Future Research Backlog: SuryaNet Version 4 Roadmap

This backlog establishes the conceptual research roadmap for Version 4 model development. These are proposed architectural experiments to be executed after the Version 3 retraining campaign is complete:

1.  **Cross-Attention Fusion Refinement**: Modify stacked multi-head cross-attention fusion block to utilize key-value projections from individual sensor encoders.
2.  **Physics-Aware Fusion**: Inject derived physical variables (such as magnetic flux density and active region classifications) directly into the late fusion classifier head.
3.  **Raw SoLEXS Sequence Encoder**: Replace binned channel rates with a high-cadence 5-second sequence encoder to capture fine-grained soft X-ray temporal details.
4.  **HEL1OS Temporal Encoder**: Encode hard X-ray count spectra using a specialized temporal convolutional network (TCN) before late fusion.
5.  **Multi-Task Joint Learning**: Retrain model to jointly predict both the occurrence of a solar flare (binary classification) and the class of the flare (ordinal regression).
6.  **Self-Supervised Pretraining**: Pretrain encoders on raw historical GOES archives (2010-2023) using masked autoencoder (MAE) self-supervision.
7.  **Telemetry Reconstruction**: Implement a generative autoencoder block to reconstruct missing SoLEXS or HEL1OS data during telemetry outages, replacing zero-padding masks.
8.  **Adaptive Sensor Weighting**: Dynamically weight sensor contributions in cross-attention based on real-time signal-to-noise ratios.
