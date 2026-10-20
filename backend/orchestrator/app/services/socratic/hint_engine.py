"""
File: orchestrator/app/services/socratic/hint_engine.py
Description: 3-Tier Progressive Hint Engine for elementary Socratic tutoring.
             Guarantees zero answer leakage across Nudge, Visual, and Micro-Breakdown tiers.
"""

import re
import logging
from typing import Optional, Dict, List, Any, Tuple
from app.services.socratic.card_schema import SocraticStep
from app.services.socratic.prompts.controller import SocraticPromptController

logger = logging.getLogger("orchestrator.socratic.hint_engine")


class HintEngine:
    """
    Manages progressive 3-tier hint generation for elementary students (Grades 1-6).
    Tier 1: Guiding Nudge (focus attention on key terms/starting values, no arithmetic)
    Tier 2: Visual Scaffold (emoji diagrams, cross-out illustrations)
    Tier 3: Micro-Breakdown (small bite-sized calculation sub-steps, no final answer)
    """

    def __init__(self, prompt_controller: Optional[SocraticPromptController] = None):
        self.prompt_controller = prompt_controller or SocraticPromptController()

    def escalate_hint(
        self,
        step: SocraticStep,
        prior_attempts: Optional[List[str]] = None,
        grade_level: str = "grade_1_3"
    ) -> Tuple[int, str]:
        """
        Advances the hint level for the step (capped at 3) and returns (new_level, hint_text).
        """
        prior_attempts = prior_attempts or []
        next_tier = min(step.current_hint_level + 1, 3)
        step.current_hint_level = next_tier

        # Use pre-computed hint if already cached in step.hints
        if next_tier <= len(step.hints) and step.hints[next_tier - 1]:
            hint_text = step.hints[next_tier - 1]
            logger.info(f"[HintEngine] Used pre-computed hint tier {next_tier}")
        else:
            hint_text = self.generate_hint(
                step=step,
                tier=next_tier,
                prior_attempts=prior_attempts,
                grade_level=grade_level
            )
            # Cache it into step.hints
            while len(step.hints) < next_tier:
                step.hints.append("")
            step.hints[next_tier - 1] = hint_text

        logger.info(f"[HintEngine] Generated hint level {next_tier} for step {step.step_number}")

        if next_tier == 3:
            try:
                from app.services.telemetry.gap_recorder import log_gap_event
                log_gap_event(
                    gap_type="learner",
                    gap_code="HINT_ESCALATION",
                    severity=1,
                    grade_tier=grade_level,
                    step_index=step.step_number,
                    details={
                        "step_title": step.title,
                        "concept": step.concept,
                        "prior_attempts": prior_attempts,
                    }
                )
            except Exception as e:
                logger.debug(f"[HintEngine] Gap log failed: {e}")

        return next_tier, hint_text

    def generate_hint(
        self,
        step: SocraticStep,
        tier: int,
        prior_attempts: Optional[List[str]] = None,
        grade_level: str = "grade_1_3"
    ) -> str:
        """
        Generates a grade-appropriate hint for the target tier.
        Uses deterministic pedagogical heuristics with LLM template fallback.
        Enforces strict zero answer leakage: Tier 1-3 hints never contain the expected answer.
        """
        prior_attempts = prior_attempts or []
        attempts_str = ", ".join(prior_attempts) if prior_attempts else "None yet"

        # 1. Deterministic elementary heuristics
        fallback_hint = self._generate_rule_based_hint(step, tier, grade_level)
        if fallback_hint:
            hint_text = fallback_hint
        else:
            # 2. LLM Prompt Controller fallback
            try:
                prompt_data = self.prompt_controller.format_prompt(
                    template_name="progressive_hint_generation",
                    grade_level=grade_level,
                    hint_tier=tier,
                    step_mission=step.mission,
                    your_turn_question=step.your_turn,
                    step_concept=step.concept or step.title,
                    prior_attempts=attempts_str
                )
                hint_text = f"💡 Think about {step.title.lower()}! Review clue: {step.clue}"
            except Exception as e:
                logger.warning(f"Error generating LLM hint: {e}. Using deterministic fallback.")
                hint_text = f"💡 Check the clue: {step.clue}"

        # Zero-leakage invariant guard: verify hint with LeakGuard
        if step.expected_answer:
            from app.services.guardrails.leak_guard import check_tutor_response_leak
            is_leak, _, reason = check_tutor_response_leak(
                tutor_reply=hint_text,
                target_answer=str(step.expected_answer),
                is_step_solved=False,
                is_reveal_state=False,
                current_hint_tier=tier,
                problem_text=f"{step.mission} {step.clue} {step.your_turn}"
            )
            if is_leak:
                logger.warning(f"[HintEngine] Leaked answer detected in hint tier {tier}: {reason}. Sanitizing.")
                hint_text = f"💡 Parallel clue: Think about our clue '{step.clue}' and apply it to a similar example step by step!"

        return hint_text

    def _generate_rule_based_hint(
        self,
        step: SocraticStep,
        tier: int,
        grade_level: str
    ) -> Optional[str]:
        """
        Generates clean visual and conceptual scaffolds without leaking expected answers.
        Tier 1: Guiding Nudge (re-focus on clue/starting values, no arithmetic)
        Tier 2: Visual Scaffold (emoji diagrams, concrete pictures, no answer disclosure)
        Tier 3: Worked Parallel Example (different numbers/objects; never active answer)
        """
        question = step.your_turn.strip()
        q_lower = question.lower() + " " + step.mission.lower() + " " + step.clue.lower()
        numbers = [int(n) for n in re.findall(r"\b\d+\b", question)]
        is_math = len(numbers) >= 2 or any(w in q_lower for w in ["plus", "minus", "subtract", "add", "count", "left", "total"])

        # Science Topic Detection
        is_boiling = any(w in q_lower for w in ["boil", "steam", "evaporat", "kettle"])
        is_melting = any(w in q_lower for w in ["melt", "ice", "popsicle", "freeze", "freezer"])
        is_plant = any(w in q_lower for w in ["plant", "sunlight", "photosynthesis", "leaf", "roots", "seed"])
        is_gravity = any(w in q_lower for w in ["gravity", "fall", "drop", "downward"])
        is_magnet = any(w in q_lower for w in ["magnet", "magnetic", "attract", "repel", "iron", "pole"])
        is_shadow = any(w in q_lower for w in ["shadow", "light", "flashlight", "beam", "dark shape"])
        is_sink_float = any(w in q_lower for w in ["sink", "float", "buoyancy", "water surface"])
        is_lifecycle = any(w in q_lower for w in ["butterfly", "caterpillar", "chrysalis", "cocoon", "frog", "tadpole"])
        is_day_night = any(w in q_lower for w in ["day and night", "night", "dark at night", "earth spin", "sun rise"])
        is_rain = any(w in q_lower for w in ["rain", "cloud", "rainbow", "water droplet", "storm"])
        is_sound = any(w in q_lower for w in ["sound", "vibration", "vibrate", "hear", "drum"])

        if tier == 1:
            # Tier 1: Guiding Nudge
            if is_boiling:
                return "👀 Clue: Think about what happens to water in a hot kettle when you see white puffy steam!"
            elif is_melting:
                return "👀 Clue: Think about what happens to an ice cube when it is left on a warm table in the sun."
            elif is_plant:
                return "👀 Clue: What shines brightly in the sky and what falls from rainclouds that plants need?"
            elif is_gravity:
                return "👀 Clue: When you drop an apple, does it float away into space or fall down to the ground?"
            elif is_magnet:
                return "👀 Clue: Look at what things stick to your refrigerator door at home!"
            elif is_shadow:
                return "👀 Clue: When you stand in front of a bright sunny light, what dark shape follows your feet?"
            elif is_sink_float:
                return "👀 Clue: Think about a wooden toy boat versus a heavy metal coin in the bathtub."
            elif is_lifecycle:
                return "👀 Clue: Think about what tiny crawling creature munches leaves before growing colorful wings."
            elif is_day_night:
                return "👀 Clue: When our side of the spinning Earth turns away from the Sun, what happens to the sky?"
            elif is_rain:
                return "👀 Clue: When billions of water drops gather up high in the sky, what fluffy shapes do they make?"
            elif is_sound:
                return "👀 Clue: Touch your throat gently while humming! What rapid buzzing or shaking do you feel?"
            elif is_math and len(numbers) >= 2:
                return f"👀 Look at the numbers in the question: {', '.join(map(str, numbers))}. What operation does our mission ask us to do?"
            return f"👀 Focus on the keyword in our mission: '{step.mission}'. What is the key thing we should find?"

        elif tier == 2:
            # Tier 2: Visual Scaffold (Zero answer disclosure)
            if is_boiling or is_melting:
                return "🎨 Visual helper:\n🧊 (Solid Ice) ➡️ [Heat 🔥] ➡️ 💧 (Liquid Water) ➡️ [More Heat 🔥] ➡️ 💨 (Steam / Gas)!"
            elif is_plant:
                return "🎨 Visual helper:\n☀️ Sunlight + 🌧️ Water + 🍃 Green Leaf ➡️ 🍬 Plant Food (Sugar) + 🌬️ Fresh Oxygen!"
            elif is_gravity:
                return "🎨 Visual helper:\n🍎 (Apple in air) ⬇️⬇️ [ Earth's Invisible Downward Pull ] ⬇️⬇️ 🌍 (Falls to Ground)!"
            elif is_magnet:
                return "🎨 Visual helper:\n🧲 [North Pole] ➡️ ❤️ ⬅️ [South Pole] (Opposite poles pull toward each other and stick together!)"
            elif is_shadow:
                return "🎨 Visual helper:\n🔦 (Light Beam) ➡️ ✋ (Hand Blocks Light) ➡️ ⬛ (Dark Shape on Wall)!"
            elif is_sink_float:
                return "🎨 Visual helper:\n🌊 Water Surface: 🪵 (Light Wood Floats 🛶) | ⬇️ 🪨 (Heavy Rock Sinks to Bottom)!"
            elif is_lifecycle:
                if "frog" in q_lower or "tadpole" in q_lower:
                    return "🎨 Visual helper:\n🥚 (Egg in Pond) ➡️ 🐟 (Swimming Baby with Tail) ➡️ 🐸 (Adult Hopping Frog)!"
                return "🎨 Visual helper:\n🥚 (Egg) ➡️ 🐛 (Caterpillar) ➡️ 🥥 (Protective Pod / Shell) ➡️ 🦋 (Butterfly)!"
            elif is_day_night:
                return "🎨 Visual helper:\n☀️ Sun Shining ➡️ 🌍 [Day Side ☀️ | Night Side 🌙] ➡️ (Earth spins once every 24 hours)!"
            elif is_rain:
                return "🎨 Visual helper:\n💧 (Water rises as vapor) ➡️ ☁️ (Clouds get heavy) ➡️ 🌧️ (Rain falls down)!"
            elif is_sound:
                return "🎨 Visual helper:\n🥁 (Drum skin shakes rapidly) 〰️〰️ (Sound waves travel through air) ➡️ 👂 (Ears hear sound)!"
            elif is_math and len(numbers) >= 2 and numbers[0] <= 15 and numbers[1] <= 15:
                a, b = numbers[0], numbers[1]
                if "-" in question or any(w in q_lower for w in ["left", "remain", "gave", "ate", "lost", "minus"]):
                    icons = "🍎 " * a
                    return f"🎨 Visual helper:\n{icons}\n❌ Imagine crossing out {b} apples! How many are left?"
                elif "+" in question or any(w in q_lower for w in ["total", "altogether", "both", "in all", "plus"]):
                    return f"🎨 Visual helper:\nGroup 1: {'⭐ ' * a}\nGroup 2: {'⭐ ' * b}\nCount both groups together!"
            return f"🎨 Let's picture it! {step.helpful_example}"

        elif tier == 3:
            # Tier 3: Worked Parallel Example (different numbers/objects, zero answer leakage)
            if is_boiling:
                return "🧩 Parallel Example: Think about a puddle on a sunny sidewalk. The sun warms the puddle until the liquid disappears into the air as misty vapor. What word describes that liquid-to-gas change?"
            elif is_melting:
                return "🧩 Parallel Example: Think about chocolate chips held in a warm hand. The solid chips absorb heat and turn into runny syrup. What word describes that solid-to-liquid change?"
            elif is_plant:
                return "🧩 Parallel Example: Just like a baker combines flour, eggs, and oven heat to bake bread, green plants combine sunlight, soil moisture, and air to make their sweet food. What is this plant food-making process called?"
            elif is_gravity:
                return "🧩 Parallel Example: If you drop a soccer ball from the top of the stairs, an invisible planetary pull brings it straight down to the floor. What invisible force is pulling it down?"
            elif is_magnet:
                return "🧩 Parallel Example: Think about how two ends of toy train cars snap together when facing the right way. What action do opposite poles do to each other?"
            elif is_shadow:
                return "🧩 Parallel Example: If you hold a textbook in front of a lamp, the textbook stops the light beams, casting a dark shape on the wall behind it."
            elif is_sink_float:
                return "🧩 Parallel Example: A heavy iron anchor drops deep to the ocean floor, while a hollow toy boat rests on top of the waves."
            elif is_lifecycle:
                if "frog" in q_lower or "tadpole" in q_lower:
                    return "🧩 Parallel Example: An eagle starts inside a speckled egg, hatches into an eaglet with soft down, and grows strong flying wings."
                return "🧩 Parallel Example: An oak tree starts as a tiny acorn in soil, sprouts green shoots, and grows into a tall tree that drops new seeds."
            elif is_day_night:
                return "🧩 Parallel Example: Imagine shining a flashlight at a toy globe. One side is bright while the other side is in darkness, until you turn the globe around."
            elif is_rain:
                return "🧩 Parallel Example: When steam from a hot shower hits a cold glass window, tiny water drops gather together and trickle down the pane."
            elif is_sound:
                return "🧩 Parallel Example: Pluck a rubber band stretched between your fingers. It shakes quickly back and forth, creating a buzzing hum you can hear!"
            elif is_math and len(numbers) >= 2:
                a, b = numbers[0], numbers[1]
                target_val = None
                if step.expected_answer:
                    try:
                        target_val = int(str(step.expected_answer).strip())
                    except ValueError:
                        pass
                forbidden = {a, b}
                if target_val is not None:
                    forbidden.add(target_val)

                if "-" in question or any(w in q_lower for w in ["left", "remain", "gave", "ate", "lost", "minus"]):
                    pa, pb = a + 4, b + 2
                    while (pa - pb) in forbidden or pa in forbidden or pb in forbidden:
                        pa += 1
                    return (
                        f"🧩 Parallel Example (different problem):\n"
                        f"If a student had {pa} crayons and shared {pb} with a friend:\n"
                        f"{pa} - {pb} = {pa - pb} crayons remaining.\n"
                        f"Now use this same take-away thinking on your problem!"
                    )
                elif "+" in question or any(w in q_lower for w in ["total", "altogether", "both", "plus", "sum"]):
                    pa, pb = a + 3, b + 2
                    while (pa + pb) in forbidden or pa in forbidden or pb in forbidden:
                        pa += 1
                    return (
                        f"🧩 Parallel Example (different problem):\n"
                        f"If you collected {pa} red leaves and {pb} yellow leaves:\n"
                        f"{pa} + {pb} = {pa + pb} leaves in total.\n"
                        f"Now use this same combining thinking on your problem!"
                    )
                elif any(w in q_lower for w in ["times", "multipl", "product", "each", "groups of", "*", "×"]):
                    pa, pb = max(2, a + 1), max(2, b + 1)
                    while (pa * pb) in forbidden or pa in forbidden or pb in forbidden:
                        pa += 1
                    return (
                        f"🧩 Parallel Example (different problem):\n"
                        f"If there are {pa} baskets with {pb} apples in each:\n"
                        f"{pa} × {pb} = {pa * pb} apples altogether.\n"
                        f"Now use this same multiplication thinking on your problem!"
                    )
                elif any(w in q_lower for w in ["divid", "split", "share equally", "/", "÷"]):
                    pb = max(2, b + 1)
                    pa = pb * 3
                    while (pa // pb) in forbidden or pa in forbidden or pb in forbidden:
                        pa += pb
                    return (
                        f"🧩 Parallel Example (different problem):\n"
                        f"If {pa} stickers are shared equally among {pb} friends:\n"
                        f"{pa} ÷ {pb} = {pa // pb} stickers each.\n"
                        f"Now use this same sharing thinking on your problem!"
                    )
            return f"🧩 Parallel Example: Think about our clue: '{step.clue}' and apply it to a similar situation step-by-step!"

        return None
