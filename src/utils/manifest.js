let object = {
    author: 'Yumata',
    github: 'https://github.com/yumata/lampa-source',
    github_lampa: 'https://yumata.github.io/lampa/',
    css_version: '2.7.0',
    app_version: '2.4.6',
    cub_site: 'localhost:8009'
}

let plugins = []

Object.defineProperty(object, 'app_digital', { get: ()=> parseInt(object.app_version.replace(/\./g,'')) })
Object.defineProperty(object, 'css_digital', { get: ()=> parseInt(object.css_version.replace(/\./g,'')) })

Object.defineProperty(object, 'plugins', { 
    get: ()=> plugins,
    set: (plugin)=> {
        if(typeof plugin == 'object' && typeof plugin.type == 'string'){
            plugins.push(plugin)
        }
    }
})

/**
 * Старые зеркала, которые не используются больше, но могут быть полезны для обратной совместимости
 */
Object.defineProperty(object, 'old_mirrors', { 
    get: ()=> ['localhost:8009'],
    set: ()=> {}
})

/**
 * Список актуальных зеркал
 */
Object.defineProperty(object, 'cub_mirrors', { 
    get: ()=> {
        let lampa = ['localhost:8009']
        let users = localStorage.getItem('cub_mirrors') || '[]'

        try {
            users = JSON.parse(users)
        } catch (e) {
            users = []
        }

        if(Object.prototype.toString.call( users ) === '[object Array]' && users.length){
            return lampa.concat(users)
        }

        return lampa
    },
    set: ()=> {}
})

/**
 * Список зеркал для сокета, вынесены отдельно, так как могут отличаться от обычных зеркал
 */
Object.defineProperty(object, 'soc_mirrors', { 
    get: ()=> ['localhost:8009'],
    set: ()=> {}
})

/**
 * Текущее доменное имя, которое используется для работы с CUB
 */
Object.defineProperty(object, 'cub_domain', { 
    get: ()=> {
        // Принудительно используем localhost для разработки
        if(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'localhost:8009'
        }
        
        let use = localStorage.getItem('cub_domain') || object.cub_site

        return use
    } 
})

export default object