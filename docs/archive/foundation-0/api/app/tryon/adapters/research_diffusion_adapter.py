from api.app.tryon.ports import InferenceInput, InferenceOutput


class CommercialLicenseViolationError(Exception):
    """Raised when an academic research-only model is invoked in a commercial production environment."""


class ResearchDiffusionAdapter:
    """Adapter wrapping academic research diffusion weights (e.g. IDM-VTON, OOTDiffusion).

    Rule I08: Research-model evaluation != production commercial authorization.
    This adapter is explicitly flagged as NOT cleared for commercial production use.
    """

    def __init__(
        self,
        model_version: str = "idm-vton-v1.0-eval",
        pipeline_version: str = "diffusion-diffusers-v0.27",
        environment: str = "test",
        allow_research_mode: bool = False,
    ) -> None:
        self._model_version = model_version
        self._pipeline_version = pipeline_version
        self.environment = environment
        self.allow_research_mode = allow_research_mode

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def pipeline_version(self) -> str:
        return self._pipeline_version

    @property
    def is_commercial_cleared(self) -> bool:
        return False

    async def execute_tryon(self, payload: InferenceInput) -> InferenceOutput:
        # Commercial License Gate
        if self.environment == "production" and not self.allow_research_mode:
            raise CommercialLicenseViolationError(
                f"Model '{self.model_version}' carries an academic non-commercial license "
                f"and is strictly forbidden in commercial production without authorization."
            )

        # In evaluation environments, execute simulation or bridge
        return InferenceOutput(
            rendered_image_bytes=payload.user_photo_bytes,
            model_version=self.model_version,
            pipeline_version=self.pipeline_version,
            inference_latency_ms=1200.0,
            raw_metadata={
                "license": "Non-Commercial / Academic Research Only",
                "adapter": "ResearchDiffusionAdapter",
            },
        )
