import os

# Define the correct content with spaces around == and visual slots
HOME_CONTENT = r"""{% extends "base.html" %}

{% block title %}Party Finder • SquadUp{% endblock %}

{% block content %}
<div class="row g-4">
  <div class="col-lg-3">
    <div class="card squadup-card">
      <div class="card-body">
        <h5 class="card-title mb-3">Filters</h5>

        <form method="get" class="vstack gap-3">
          <div>
            <label class="form-label text-secondary">Game</label>
            <select class="form-select squadup-input" name="game">
              <option value="">All</option>
              {% for v, label in game_choices %}
                <option value="{{ v }}" {% if filters.game == v %}selected{% endif %}>{{ label }}</option>
              {% endfor %}
            </select>
          </div>

          <div>
            <label class="form-label text-secondary">Required rank</label>
            <select class="form-select squadup-input" name="rank">
              <option value="">Any</option>
              {% for v, label in rank_choices %}
                <option value="{{ v }}" {% if filters.rank == v %}selected{% endif %}>{{ label }}</option>
              {% endfor %}
            </select>
          </div>

          <div>
            <label class="form-label text-secondary">Role</label>
            <select class="form-select squadup-input" name="role">
              <option value="">Any</option>
              {% for v, label in role_choices %}
                <option value="{{ v }}" {% if filters.role == v %}selected{% endif %}>{{ label }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="form-check">
            <input class="form-check-input squadup-check" type="checkbox" value="1" id="mic" name="mic" {% if filters.mic == "1" %}checked{% endif %}>
            <label class="form-check-label" for="mic">Has mic</label>
          </div>

          <div class="d-grid gap-2">
            <button class="btn btn-neon" type="submit">Apply</button>
            <a class="btn btn-outline-purple" href="{% url 'home' %}">Reset</a>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div class="col-lg-9">
    <div class="d-flex align-items-center justify-content-between mb-3">
      <div>
        <h2 class="mb-0">Party Finder</h2>
        <div class="text-secondary small">Browse active parties and join if you fit.</div>
      </div>
      <a class="btn btn-neon" href="{% url 'lobby_create' %}">+ Create Party</a>
    </div>

    <div class="lobby-grid">
      {% for lobby in lobbies %}
        <div class="lobby-card">
          <!-- Header Banner -->
          <div class="lobby-card-header">
            <div class="lobby-card-avatar">
              {{ lobby.host.username|slice:":1"|upper }}
            </div>
          </div>

          <!-- Body -->
          <div class="lobby-stats">
            <div class="lobby-title" title="{{ lobby.title }}">{{ lobby.title }}</div>
            
            <div class="lobby-meta">
              <span>Host: {{ lobby.host.username }}</span>
              {% if lobby.mic_required %}
                <span class="text-info">• Mic</span>
              {% endif %}
            </div>

            <div class="lobby-badges">
              <div class="faceit-badge">{{ lobby.get_game_display }}</div>
              <div class="faceit-badge">{{ lobby.get_required_rank_display }}</div>
              <div class="faceit-badge text-white border-0" style="background: transparent; color: #a1a1aa;">
                {{ lobby.get_required_role_display }}
              </div>
            </div>
          </div>

          <!-- Visual Slots Footer -->
           <div class="slot-container">
             {% for slot_user in lobby.get_slots %}
               {% if slot_user %}
                 <div class="slot-circle filled" title="{{ slot_user.username }}">
                   {% if slot_user.gamer_profile.avatar %}
                      <!-- Assuming avatar URL exists, or use initial -->
                      {{ slot_user.username|slice:":1"|upper }}
                   {% else %}
                      {{ slot_user.username|slice:":1"|upper }}
                   {% endif %}
                 </div>
               {% else %}
                 <!-- Empty Slot -->
                 <div class="slot-circle empty">
                    {% if user.is_authenticated and lobby.status != 'ended' and lobby.id not in my_lobby_ids %}
                      <form method="post" action="{% url 'lobby_join' lobby.id %}" style="width:100%; height:100%;">
                        {% csrf_token %}
                        <button class="slot-join-btn" type="submit" title="Join Slot">+</button>
                      </form>
                    {% else %}
                      <span style="opacity: 0.3;">+</span>
                    {% endif %}
                 </div>
               {% endif %}
             {% endfor %}
             
             <!-- Leave/Status Actions if joined -->
             {% if user.is_authenticated and lobby.id in my_lobby_ids %}
                <div class="ms-auto">
                  <span class="badge squadup-badge-purple">Joined</span>
                </div>
             {% endif %}
           </div>
           
           <!-- Clickable Overlay -->
           <a href="{% url 'lobby_detail' lobby.id %}" class="stretched-link" style="position: absolute; top: 0; left: 0; width: 100%; height: 80px; z-index: 1;"></a>
        </div>
      {% empty %}
        <div class="col-12">
          <div class="card squadup-card">
            <div class="card-body">
              <div class="text-center py-5">
                <h4 class="text-white">No active lobbies</h4>
                <div class="text-secondary mb-3">Be the first to start a match!</div>
                <a class="btn btn-neon" href="{% url 'lobby_create' %}">Create Lobby</a>
              </div>
            </div>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
"""

path = r"c:\Users\Bosco\Desktop\Party_Finder\templates\home.html"
with open(path, 'w', encoding='utf-8') as f:
    f.write(HOME_CONTENT)

print(f"Force updated {path}")
