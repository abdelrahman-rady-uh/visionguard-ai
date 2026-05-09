import os
from PIL import Image
from backend.utils.security import normalize_confidence


class CaptionService:
    def __init__(self):
        self.ready = False
        self.reason = "fallback"
        self._attempted = False
        self.torch = None

        self.blip_processor = None
        self.blip_model = None

        self.vit_processor = None
        self.vit_model = None
        self.vit_tokenizer = None

    def _try_load_transformer(self):
        if self._attempted:
            return
        self._attempted = True

        try:
            import torch
            self.torch = torch
        except Exception as exc:
            self.ready = False
            self.reason = f"fallback:{exc.__class__.__name__}"
            return

        local_only = os.getenv("CAPTION_REMOTE_LOAD", "1") != "1"

        # Higher-quality BLIP first.
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration

            model_id = "Salesforce/blip-image-captioning-base"
            self.blip_processor = BlipProcessor.from_pretrained(model_id, local_files_only=local_only)
            self.blip_model = BlipForConditionalGeneration.from_pretrained(model_id, local_files_only=local_only)
            self.blip_model.eval()
            self.ready = True
            self.reason = "blip"
            return
        except Exception:
            pass

        # Stable fallback caption model.
        try:
            from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

            model_id = "nlpconnect/vit-gpt2-image-captioning"
            self.vit_model = VisionEncoderDecoderModel.from_pretrained(model_id, local_files_only=local_only)
            self.vit_processor = ViTImageProcessor.from_pretrained(model_id, local_files_only=local_only)
            self.vit_tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=local_only)
            self.vit_model.eval()
            self.ready = True
            self.reason = "vit-gpt2"
            return
        except Exception as exc:
            self.ready = False
            self.reason = f"fallback:{exc.__class__.__name__}"

    def _fallback_caption(self, frame):
        mean_brightness = float(frame.mean())
        red_dom = float(frame[..., 0].mean())
        green_dom = float(frame[..., 1].mean())
        blue_dom = float(frame[..., 2].mean())

        tone = "dark" if mean_brightness < 80 else "bright" if mean_brightness > 170 else "normal-lit"
        if red_dom > green_dom + 12 and red_dom > blue_dom + 12:
            color_hint = "with warm dominant colors"
        elif blue_dom > red_dom + 12 and blue_dom > green_dom + 12:
            color_hint = "with cool dominant colors"
        else:
            color_hint = "with balanced colors"

        text = f"A {tone} video scene {color_hint}."
        return text, 58.0

    def _caption_frame(self, frame):
        if not self._attempted:
            self._try_load_transformer()

        image = Image.fromarray(frame)
        if self.ready and self.blip_model is not None and self.blip_processor is not None:
            try:
                inputs = self.blip_processor(images=image, return_tensors="pt")
                with self.torch.no_grad():
                    out = self.blip_model.generate(**inputs, max_new_tokens=28, num_beams=4)
                caption = self.blip_processor.tokenizer.decode(out[0], skip_special_tokens=True).strip()
                if caption:
                    return caption, 92.0
            except Exception:
                pass

        if self.ready and self.vit_model is not None and self.vit_processor is not None and self.vit_tokenizer is not None:
            try:
                pixel_values = self.vit_processor(images=[image], return_tensors="pt").pixel_values
                with self.torch.no_grad():
                    output_ids = self.vit_model.generate(pixel_values, max_length=26, num_beams=4)
                caption = self.vit_tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
                if caption:
                    return caption, 87.0
            except Exception:
                pass

        return self._fallback_caption(frame)

    def generate_caption(self, frames):
        if not frames:
            return {"caption": "No visual content detected.", "confidence": 0.0}
        frame = frames[len(frames) // 2]
        caption, conf = self._caption_frame(frame)
        return {"caption": caption, "confidence": normalize_confidence(conf)}

    def caption_from_frame(self, frame):
        caption, conf = self._caption_frame(frame)
        return {"caption": caption, "confidence": normalize_confidence(conf)}
