#!/bin/bash

# скрипт для установки пароля и почты для root пользователя, ник пользователя - root
# перед использованием в контейнере лучше немного подождать до инициализации gitlab-ce, сразу может не сработать

set -e

echo "Смена пароля root..."

echo -e "$ROOT_PASSWORD\n$ROOT_PASSWORD" | gitlab-rake "gitlab:password:reset[root]"

echo "Смена почты root..."

gitlab-rails runner "
    user = User.find(1);
    user.email = '$ROOT_EMAIL';
    user.skip_reconfirmation!;
    user.save!
"

echo "Настройки переменных..."
curl --header "PRIVATE-TOKEN: $GITLAB_ROOT_TOKEN" \
     --request POST "http://localhost/api/v4/projects/$PROJECT_ID/variables" \
     --form "key=SSH_PRIVATE_KEY" \
     --form "value=$MY_SECRET_KEY"


echo "Настройки безопасности..."

gitlab-rails runner "ApplicationSetting.last.update(signup_enabled: false)"

echo "Все готово!"