import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

HOME_HTML = r"""{% extends "base.html" %}

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

          <!-- Footer / Status -->
           <div class="faceit-status">
             <div class="d-flex align-items-center gap-2">
                <span class="{% if lobby.status == 'full' %}text-warning{% else %}text-success{% endif %} fw-bold">
                  {{ lobby.slots_filled }}/{{ lobby.slots_total }}
                </span>
                <span class="small text-secondary">{{ lobby.get_status_display }}</span>
             </div>

             {% if user.is_authenticated and lobby.status != 'ended' %}
                {% if lobby.id in my_lobby_ids %}
                  <span class="badge squadup-badge-purple">Joined</span>
                {% else %}
                  <form method="post" action="{% url 'lobby_join' lobby.id %}">
                    {% csrf_token %}
                    <button class="faceit-action" type="submit" {% if lobby.status == 'full' %}disabled{% endif %}>
                      Join
                    </button>
                  </form>
                {% endif %}
             {% else %}
                <a href="{% url 'lobby_detail' lobby.id %}" class="btn btn-outline-secondary btn-sm" style="font-size: 0.7rem; border-color: #3f3f46;">View</a>
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

LOBBY_DETAIL_HTML = r"""{% extends "base.html" %}

{% block title %}{{ lobby.title }} • SquadUp{% endblock %}

{% block content %}
<div class="row g-4">
  <div class="col-lg-8">
    <div class="card squadup-card">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="d-flex gap-2 mb-2 flex-wrap">
              <span class="badge squadup-badge">{{ lobby.get_game_display }}</span>
              <span class="badge squadup-badge-purple">{{ lobby.get_required_rank_display }}</span>
              {% if lobby.mic_required %}<span class="badge squadup-badge-purple">Mic</span>{% endif %}
            </div>
            <h2 class="mb-1">{{ lobby.title }}</h2>
            <div class="text-secondary small">Hosted by <span class="text-light">{{ lobby.host.username }}</span></div>
          </div>

          <div class="text-end">
            <div class="small text-secondary">Slots</div>
            <div class="fw-semibold">{{ lobby.slots_filled }}/{{ lobby.slots_total }}</div>
            <div class="small {% if lobby.status == 'full' %}text-warning{% elif lobby.status == 'ended' %}text-secondary{% else %}text-success{% endif %}">
              {{ lobby.get_status_display }}
            </div>
          </div>
        </div>

        {% if lobby.description %}
          <hr class="squadup-hr">
          <div class="text-secondary">{{ lobby.description|linebreaksbr }}</div>
        {% endif %}

        <hr class="squadup-hr">

        <div class="d-flex gap-2 flex-wrap">
          {% if user.is_authenticated %}
            {% if is_participant %}
              {% if lobby.host_id != user.id %}
                <form method="post" action="{% url 'lobby_leave' lobby.id %}">
                  {% csrf_token %}
                  <button class="btn btn-outline-purple" type="submit">Leave Lobby</button>
                </form>
              {% else %}
                <form method="post" action="{% url 'lobby_end' lobby.id %}">
                  {% csrf_token %}
                  <button class="btn btn-outline-purple" type="submit" {% if lobby.status == 'ended' %}disabled{% endif %}>End Lobby</button>
                </form>
              {% endif %}
            {% else %}
              <form method="post" action="{% url 'lobby_join' lobby.id %}">
                {% csrf_token %}
                <button class="btn btn-neon" type="submit" {% if lobby.status == 'full' or lobby.status == 'ended' %}disabled{% endif %}>Join</button>
              </form>
            {% endif %}
          {% else %}
            <a class="btn btn-neon" href="{% url 'login' %}?next={% url 'lobby_detail' lobby.id %}">Login to Join</a>
          {% endif %}
          <a class="btn btn-outline-neon" href="{% url 'home' %}">Back</a>
        </div>
      </div>
    </div>

    <div class="card squadup-card mt-4">
      <div class="card-body">
        <h5 class="mb-3">Players in lobby</h5>
        <div class="list-group list-group-flush">
          {% for p in participants %}
            <div class="list-group-item squadup-list-item d-flex justify-content-between align-items-center">
              <div>
                <div class="fw-semibold">{{ p.user.username }}</div>
                {% if p.user.gamer_profile %}
                  <div class="text-secondary small">
                    {{ p.user.gamer_profile.get_main_game_display }} • {{ p.user.gamer_profile.rank|default:"Unranked" }}
                  </div>
                {% endif %}
              </div>
              {% if p.user.gamer_profile %}
                <span class="badge squadup-badge-purple">{{ p.user.gamer_profile.reputation_badge }}</span>
              {% endif %}
            </div>
          {% empty %}
            <div class="text-secondary">No participants yet.</div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

  <div class="col-lg-4">
    <div class="card squadup-card mb-4">
      <div class="card-body">
        <h5 class="mb-2">Host contact</h5>
        {% if reveal_host_contacts and host_profile %}
          <div class="text-secondary small mb-2">Visible because you joined.</div>
          <div class="vstack gap-2">
            <div class="squadup-contact">
              <div class="text-secondary small">Discord</div>
              <div class="fw-semibold">{{ host_profile.discord_id|default:"Not set" }}</div>
            </div>
            <div class="squadup-contact">
              <div class="text-secondary small">Steam</div>
              {% if host_profile.steam_id %}
                <a class="link-neon" href="https://steamcommunity.com/profiles/{{ host_profile.steam_id }}" target="_blank" rel="noopener">
                  View profile
                </a>
              {% else %}
                <div class="fw-semibold">Not set</div>
              {% endif %}
            </div>
          </div>
        {% else %}
          <div class="text-secondary">Join the lobby to reveal host contact info.</div>
        {% endif %}
      </div>
    </div>

    <!-- Lobby Chat Card -->
    <div class="card squadup-card" style="height: 500px; display: flex; flex-direction: column;">
        <div class="card-body p-0 d-flex flex-column h-100">
             <div class="p-3 border-bottom border-secondary-subtle">
                <h5 class="mb-0">Lobby Chat</h5>
             </div>
             
             <div class="flex-grow-1 p-3 overflow-auto" id="chat-messages"
                  hx-get="{% url 'lobby_chat_messages' lobby.id %}"
                  hx-trigger="load, every 3s">
                  <!-- Messages load here -->
                  <div class="text-center text-muted small mt-5">Loading chat...</div>
             </div>

             <div class="p-3 border-top border-secondary-subtle">
               {% if user.is_authenticated %}
               <form hx-post="{% url 'lobby_chat_send' lobby.id %}" 
                     hx-target="#chat-messages" 
                     hx-on::after-request="this.reset()">
                 {% csrf_token %}
                 <div class="input-group">
                   <input type="text" name="content" class="form-control squadup-input" placeholder="Message..." required autocomplete="off">
                   <button class="btn btn-neon" type="submit">Send</button>
                 </div>
               </form>
               {% else %}
                 <div class="text-center small text-muted">
                     <a href="{% url 'login' %}?next={{ request.path }}" class="link-neon">Login</a> to chat
                 </div>
               {% endif %}
             </div>
        </div>
    </div>

  </div>
</div>
{% endblock %}
"""

home_path = os.path.join(TEMPLATES_DIR, "home.html")
lobby_detail_path = os.path.join(TEMPLATES_DIR, "lobbies", "lobby_detail.html")

with open(home_path, "w", encoding="utf-8") as f:
    f.write(HOME_HTML)
print(f"Updated {home_path}")

with open(lobby_detail_path, "w", encoding="utf-8") as f:
    f.write(LOBBY_DETAIL_HTML)
print(f"Updated {lobby_detail_path}")
